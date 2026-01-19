import "./globals.css";
import TopNav from "@/components/TopNav";

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <TopNav />
        <main className="mx-auto max-w-5xl px-6 py-10">
          {children}
        </main>
      </body>
    </html>
  );
}
