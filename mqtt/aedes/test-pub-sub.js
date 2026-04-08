#!/usr/bin/env node
/** Quick pub/sub test to verify Aedes broker routing */
const mqtt = require('mqtt')
const client = mqtt.connect('mqtt://127.0.0.1:1883', {
  clientId: 'aedes-test-client',
  clean: true,
  protocolVersion: 4,  // MQTT 3.1.1
})

client.on('connect', () => {
  console.log('✓ Connected to Aedes broker on 1883')
  client.subscribe('friday/command/vanguard', { qos: 2 }, (err) => {
    if (err) {
      console.error('Subscribe error:', err)
    } else {
      console.log('✓ Subscribed to friday/command/vanguard')
      // Give broker a moment to register subscription
      setTimeout(() => {
        client.publish('friday/command/vanguard', JSON.stringify({
          sender: 'Friday',
          command: 'Acknowledge Genesis',
          message: 'I see you, Vanguard. The Matrix is online.'
        }), { qos: 2 }, (err) => {
          if (err) console.error('Publish error:', err)
          else console.log('✓ Published First Contact message')
        })
      }, 500)
    }
  })
})

client.on('message', (topic, message) => {
  console.log('✓ MESSAGE RECEIVED!')
  console.log('  Topic:', topic)
  console.log('  Payload:', message.toString())
  client.end()
  process.exit(0)
})

client.on('error', (err) => {
  console.error('Client error:', err)
  process.exit(1)
})

setTimeout(() => {
  console.log('TIMEOUT — no message received after 8 seconds')
  client.end()
  process.exit(1)
}, 8000)
