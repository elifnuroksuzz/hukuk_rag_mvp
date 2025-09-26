import './globals.css'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Hukuk RAG Asistanı',
  description: 'Türk Hukuk Belgeleri AI Analizi',
}

export const viewport = {
  width: 'device-width',
  initialScale: 1,
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="tr">
      <body className="font-sans antialiased">
        {children}
      </body>
    </html>
  )
}