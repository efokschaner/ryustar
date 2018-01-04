/*
dev_appserver.py has a number of incompatibilities with being hosted on a network via a real hostname
- admin server has some pretty inflexible Origin header checking that
  is tightly coupled to its --admin_host, --admin_port params
- The app server also has coupling of its task queue implementation to incoming Host headers
Therefore we try to host it in such a way that it believes and responds as if all interactions
are from/to 127.0.0.1, by rewriting Host headers and just for Admin server removing Origin headers.
We leave Origin header unmodified for the main app so we don't interfere with whatever Origin logic
the App wishes to do.

The above, does however introduce a couple more issues that need workarounds:
- The /_ah/login redirect system uses absolute Location redirect urls that 127.0.0.1
- The /_ah/login html page includes an html form with actions that have an absolute url of 127.0.0.1
To work around these we rewrite those Location headers and also modify the HTML responses

Originally I tried to work around this all just using kubernetes' nginx ingress configuration.
However, at the point I realised we'd have to modify HTML streams it became much simpler to give the dev_appserver
its own dedicated reverse proxy.
*/

let express = require('express')
let harmon = require('harmon')
let httpProxy = require('http-proxy')
let morgan = require('morgan')

process.on('unhandledRejection', error => {
  throw error
})

// returns an express middleware
// rewrites known places where the dev_appserver leaks its own hostname in to the
// content of served pages
function createRewriter (targetPort) {
  let responseSelectors = [{
    query: `form[action^="http://127\\.0\\.0\\.1:${targetPort}"]`,
    func: function (node, req, res) {
      node.getAttribute('action', function (actionValue) {
        // Make the URL relative by stripping everything up to and including host
        let prefixLength = `http://127.0.0.1:${targetPort}`.length
        let relative = actionValue.substring(prefixLength)
        node.setAttribute('action', relative)
      })
    }
  }]
  // Additional `true` parameter can be used to ignore js and css files.
  return harmon([], responseSelectors, true)
}

// returns an express application
function createProxyApp (targetPort, requestHeaderOverrides, moreMiddleware) {
  let app = express()
  app.use(morgan('tiny'))

  if (moreMiddleware !== undefined) {
    app.use(moreMiddleware.path, moreMiddleware.middleware)
  }

  var proxy = httpProxy.createProxyServer({
    target: `http://127.0.0.1:${targetPort}`,
    changeOrigin: true, // This rewrites Host header (not Origin header...)
    autoRewrite: true,
    headers: requestHeaderOverrides
  })

  app.all('*', function (req, res) {
    proxy.web(req, res)
  })

  return app
}

async function main () {
  let listenPortString = process.env.PROXY_LISTEN_PORT
  let listenPort = parseInt(listenPortString)

  let targetPortString = process.env.PROXY_TARGET_PORT
  let targetPort = parseInt(targetPortString)

  let adminListenPortString = process.env.ADMIN_PROXY_LISTEN_PORT
  let adminListenPort = parseInt(adminListenPortString)

  let adminTargetPortString = process.env.ADMIN_PROXY_TARGET_PORT
  let adminTargetPort = parseInt(adminTargetPortString)

  let rewriterMiddleware = {
    // Only use on the /_ah stuff which is written by google so we dont create / mask issues in developer's code
    path: '/_ah/',
    middleware: createRewriter(targetPort)
  }

  let proxyApp = createProxyApp(targetPort, {}, rewriterMiddleware)
  let adminProxyApp = createProxyApp(adminTargetPort, {origin: ''})

  let proxyServer = proxyApp.listen(listenPort, '0.0.0.0')
  let adminProxyServer = adminProxyApp.listen(adminListenPort, '0.0.0.0')

  async function handleShutdown () {
    console.log('Received signal. Shutting down.')
    proxyServer.close()
    adminProxyServer.close()
  }

  process.on('SIGINT', handleShutdown)
  process.on('SIGTERM', handleShutdown)

  console.info('dev-appserver-proxy is fully initialised')
}

if (require.main === module) {
  main()
}
