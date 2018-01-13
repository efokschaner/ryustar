const { createLogger, format, transports } = require('winston')

let gcloudFormat = format.printf(
  info => {
    return JSON.stringify(Object.assign({ severity: info.level }, info))
  }
)

let logger = createLogger({
  format: gcloudFormat,
  transports: [
    new transports.Console({
      handleExceptions: true
    })
  ],
  handleExceptions: true
})

module.exports = logger
