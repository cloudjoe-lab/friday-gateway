#!/usr/bin/env node
/**
 * Aedes MQTT Broker — explicit TCP server approach
 * Acts as the Universal Event Bus — Medallion Architecture V3
 */
const Aedes = require('aedes').Aedes
const net = require('net')

const aedes = new Aedes()
const PORT = process.env.MQTT_PORT || 1883

aedes.on('client', (client) => {
  console.log(`[aedes] Client connected: ${client.id}`)
})

aedes.on('clientDisconnect', (client) => {
  console.log(`[aedes] Client disconnected: ${client.id}`)
})

aedes.on('publish', (packet, client) => {
  if (client) {
    console.log(`[aedes] ${client.id} → ${packet.topic}: ${packet.payload.toString().slice(0, 80)}`)
  }
})

aedes.on('subscribe', (subscriptions, client) => {
  console.log(`[aedes] ${client.id} subscribed: ${subscriptions.map(s => s.topic).join(', ')}`)
})

const server = net.createServer(aedes.handle)

server.on('error', (err) => {
  console.error('[aedes] TCP server error:', err)
  process.exit(1)
})

server.on('listening', () => {
  const addr = server.address()
  console.log(`✜ AEDES MQTT Broker running on port ${addr.port}`)
  console.log(`   Universal Event Bus — Medallion Architecture V3`)
})

server.listen(PORT, '0.0.0.0', () => {
  // This is the listening callback
})

process.on('SIGTERM', () => {
  console.log('[aedes] SIGTERM')
  server.close(() => aedes.close())
  process.exit(0)
})

process.on('SIGINT', () => {
  console.log('[aedes] SIGINT')
  server.close(() => aedes.close())
  process.exit(0)
})
