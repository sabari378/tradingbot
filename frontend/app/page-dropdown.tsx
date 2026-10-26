'use client';

import { PanelsTopLeft } from 'lucide-react';
import { usePathname, useRouter } from 'next/navigation';

const pages = [
  { href: '/', label: 'Dashboard' },
  { href: '/chart', label: 'Chart' },
  { href: '/history', label: 'History' },
  { href: '/tests', label: 'Tests' },
  { href: '/strategy', label: 'Strategy' },
];

export function PageDropdown() {
  const pathname = usePathname();
  const router = useRouter();

  return (
    <label className="page-dropdown">
      <PanelsTopLeft size={15} aria-hidden="true" />
      <span className="sr-only">Open page</span>
      <select value={pathname} onChange={(event) => router.push(event.target.value)} aria-label="Open page">
        {pages.map((page) => <option key={page.href} value={page.href}>{page.label}</option>)}
      </select>
    </label>
  );
}
