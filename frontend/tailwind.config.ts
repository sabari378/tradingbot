import type { Config } from 'tailwindcss';
const config: Config = { content: ['./app/**/*.{ts,tsx}', './components/**/*.{ts,tsx}'], theme: { extend: { colors: { ink: '#091116', panel: '#111d23', mint: '#80e4c2', amber: '#f2b866' } } }, plugins: [] };
export default config;
