import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({ subsets: ['latin', 'cyrillic'] });

export const metadata: Metadata = {
  title: 'Газпромбанк | Контроль тональности',
  description: 'Дашборд для анализа тональности отзывов клиентов Газпромбанка',
  keywords: 'Газпромбанк, аналитика, отзывы, тональность, дашборд',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ru">
      <body className={`${inter.className} bg-gray-100 min-h-screen`}>
        {children}
      </body>
    </html>
  );
}
