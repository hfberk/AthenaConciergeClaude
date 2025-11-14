import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Athena - Your Garden of Excellence',
  description: 'AI-powered concierge platform nurturing high-net-worth client relationships',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
