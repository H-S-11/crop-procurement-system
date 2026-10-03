import type { Metadata } from 'next';
import './globals.css';
import 'maplibre-gl/dist/maplibre-gl.css';

export const metadata: Metadata = {
  title: 'Thanjavur Procurement Intelligence',
  description: 'Single-page operational dashboard for Thanjavur paddy procurement officers — live DPC forecasts, storage capacity, risk tiers, and flood exposure.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="scroll-smooth">
      <head>
        <link rel="preconnect" href="https://basemaps.cartocdn.com" />
      </head>
      <body className="antialiased min-h-screen bg-slate-50 text-slate-900 pb-20">
        {/* Content wrapper */}
        <div className="w-full">
          {children}
        </div>
      </body>
    </html>
  );
}
