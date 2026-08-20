import type { Metadata } from 'next';
import './globals.css';
import { Sidebar } from '@/components/Sidebar';
import { Header } from '@/components/Header';

export const metadata: Metadata = {
  title: 'AssetPilot AI - AI Market Intelligence & Portfolio Assistant',
  description: 'Personal-first AI Market Intelligence & Portfolio Assistant covering Crypto, Stocks, and Tokenized Exposure.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-[#0b0f19] text-gray-100 antialiased flex min-h-screen">
        <Sidebar />
        <div className="flex-1 flex flex-col min-w-0">
          <Header />
          <main className="flex-1 p-6 overflow-y-auto">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
