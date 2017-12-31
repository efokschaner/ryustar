
export function start (url, onData) {
  let websocket = new WebSocket(url)

  websocket.onopen = function () {
    console.log('ws connected')
  }

  websocket.onmessage = function (evt) {
    onData(JSON.parse(evt.data))
  }

  websocket.onerror = function (evt) {
    console.error('ws error: ' + evt.data)
  }

  websocket.onclose = function (evt) {
    console.info('ws closed: ' + evt.data)
  }
}
