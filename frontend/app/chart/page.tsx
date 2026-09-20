'use client';

import Link from 'next/link';
import { Camera, ChartCandlestick, RefreshCw } from 'lucide-react';
import {
  CandlestickSeries,
  ColorType,
  createChart,
  createSeriesMarkers,
  IChartApi,
  LineSeries,
  SeriesMarker,
  Time,
  UTCTimestamp,
} from 'lightweight-charts';
import { useCallback, useEffect, useRef, useState } from 'react';

import { PageDropdown } from '../page-dropdown';

type Candle = { time: number; open: number; high: number; low: number; close: number };
type Swing = { time: number; price: number; kind: 'HH' | 'LH' | 'HL' | 'LL' };
type StructureBreak = { time: number; price: number; direction: 'bullish' | 'bearish'; label: string };
type Pattern = {
  type: 'double_top'; label: string; first_time: number; second_time: number; trigger_time: number;
  first_peak: number; second_peak: number; neckline: number;
};
type ChartPayload = {
  symbol: string; timeframe: string; candles: Candle[];
  annotations: { swings: Swing[]; breaks: StructureBreak[]; patterns: Pattern[] };
};

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? (process.env.NODE_ENV === 'development' ? 'http://127.0.0.1:8000' : '');
const timeframes = ['M5', 'M15', 'H1'] as const;
const maxCandles = 5000;
const initialVisibleCandles = 180;

export default function ChartPage() {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const [symbol, setSymbol] = useState('GOLD.i#');
  const [timeframe, setTimeframe] = useState<(typeof timeframes)[number]>('M15');
  const [payload, setPayload] = useState<ChartPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showSwings, setShowSwings] = useState(true);
  const [showBreaks, setShowBreaks] = useState(true);
  const [showPatterns, setShowPatterns] = useState(true);
  const [saved, setSaved] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const response = await fetch(`${apiUrl}/api/v1/market/chart?symbol=${encodeURIComponent(symbol)}&timeframe=${timeframe}&limit=${maxCandles}`);
      const body = await response.json();
      if (!response.ok) throw new Error(body.detail ?? 'Chart data unavailable');
      setPayload(body);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Chart data unavailable');
    } finally {
      setLoading(false);
    }
  }, [symbol, timeframe]);

  useEffect(() => { void load(); }, [load]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container || !payload) return;
    const chart = createChart(container, {
      width: container.clientWidth,
      height: container.clientHeight,
      layout: {
        attributionLogo: true,
        background: { type: ColorType.Solid, color: '#071719' },
        textColor: '#a9bbb6',
      },
      grid: { vertLines: { color: 'rgba(197,235,222,.06)' }, horzLines: { color: 'rgba(197,235,222,.08)' } },
      rightPriceScale: { borderColor: 'rgba(197,235,222,.22)' },
      timeScale: {
        borderColor: 'rgba(197,235,222,.22)',
        timeVisible: true,
        secondsVisible: false,
        rightOffset: 8,
        barSpacing: 7,
        minBarSpacing: 1,
      },
      crosshair: { vertLine: { color: '#78d9c1' }, horzLine: { color: '#78d9c1' } },
    });
    chartRef.current = chart;
    const series = chart.addSeries(CandlestickSeries, {
      upColor: '#65d6ad', downColor: '#e77b72', wickUpColor: '#65d6ad', wickDownColor: '#e77b72',
      borderUpColor: '#65d6ad', borderDownColor: '#e77b72',
    });
    series.setData(payload.candles.map((candle) => ({ ...candle, time: candle.time as UTCTimestamp })));

    const markers: SeriesMarker<Time>[] = [];
    if (showSwings) payload.annotations.swings.forEach((swing) => markers.push({
      time: swing.time as UTCTimestamp,
      position: swing.kind.endsWith('H') ? 'aboveBar' : 'belowBar',
      color: swing.kind.startsWith('H') ? '#f6c879' : '#86d9ff',
      shape: 'circle', text: swing.kind,
    }));
    if (showBreaks) payload.annotations.breaks.forEach((item) => markers.push({
      time: item.time as UTCTimestamp,
      position: item.direction === 'bullish' ? 'belowBar' : 'aboveBar',
      color: item.direction === 'bullish' ? '#a9f2d4' : '#ff9e98',
      shape: item.direction === 'bullish' ? 'arrowUp' : 'arrowDown', text: item.label,
    }));
    if (showPatterns) payload.annotations.patterns.forEach((pattern) => markers.push({
      time: pattern.trigger_time as UTCTimestamp, position: 'aboveBar', color: '#f6c879', shape: 'square', text: pattern.label,
    }));
    markers.sort((left, right) => Number(left.time) - Number(right.time));
    createSeriesMarkers(series, markers);

    if (showPatterns) payload.annotations.patterns.slice(-6).forEach((pattern) => {
      const peakLine = chart.addSeries(LineSeries, { color: '#f6c879', lineWidth: 2, lineStyle: 2, lastValueVisible: false, priceLineVisible: false });
      peakLine.setData([
        { time: pattern.first_time as UTCTimestamp, value: pattern.first_peak },
        { time: pattern.second_time as UTCTimestamp, value: pattern.second_peak },
      ]);
      const neckline = chart.addSeries(LineSeries, { color: '#e77b72', lineWidth: 1, lineStyle: 2, lastValueVisible: false, priceLineVisible: false });
      neckline.setData([
        { time: pattern.first_time as UTCTimestamp, value: pattern.neckline },
        { time: pattern.trigger_time as UTCTimestamp, value: pattern.neckline },
      ]);
    });
    const lastIndex = payload.candles.length - 1;
    chart.timeScale().setVisibleLogicalRange({
      from: Math.max(0, lastIndex - initialVisibleCandles + 1),
      to: lastIndex + 8,
    });
    const resize = new ResizeObserver(() => chart.applyOptions({ width: container.clientWidth, height: container.clientHeight }));
    resize.observe(container);
    return () => { resize.disconnect(); chart.remove(); chartRef.current = null; };
  }, [payload, showSwings, showBreaks, showPatterns]);

  const saveSnapshot = () => {
    const canvas = chartRef.current?.takeScreenshot(true, false);
    if (!canvas) return;
    const link = document.createElement('a');
    const timestamp = new Date().toISOString().replaceAll(':', '-').replaceAll('.', '-');
    link.download = `${payload?.symbol ?? symbol}-${timeframe}-patterns-${timestamp}.png`;
    link.href = canvas.toDataURL('image/png');
    link.click();
    setSaved(link.download);
  };

  return <main className="chart-page">
    <nav className="chart-nav">
      <Link href="/" className="chart-brand"><span><ChartCandlestick size={20} /></span><strong>NIRV</strong></Link>
      <PageDropdown />
    </nav>
    <section className="chart-toolbar" aria-label="Chart controls">
      <div className="chart-identity"><p>PRICE ACTION / MARKET STRUCTURE</p><h1>{payload?.symbol ?? symbol} <span>{timeframe}</span></h1></div>
      <div className="chart-controls">
        <label className="symbol-field"><span>SYMBOL</span><input value={symbol} onChange={(event) => setSymbol(event.target.value)} onKeyDown={(event) => { if (event.key === 'Enter') void load(); }} /></label>
        <div className="timeframe-control" aria-label="Timeframe">{timeframes.map((item) => <button key={item} className={timeframe === item ? 'active' : ''} onClick={() => setTimeframe(item)}>{item}</button>)}</div>
        <button className="chart-icon-button" onClick={() => void load()} aria-label="Refresh chart" title="Refresh chart"><RefreshCw size={17} className={loading ? 'spin' : ''} /></button>
        <button className="snapshot-button" onClick={saveSnapshot} disabled={!payload} title="Save pattern snapshot"><Camera size={17} /><span>SNAPSHOT</span></button>
      </div>
    </section>
    <section className="annotation-bar">
      <div className="annotation-toggles">
        <label><input type="checkbox" checked={showSwings} onChange={(event) => setShowSwings(event.target.checked)} /> SWINGS</label>
        <label><input type="checkbox" checked={showBreaks} onChange={(event) => setShowBreaks(event.target.checked)} /> BOS</label>
        <label><input type="checkbox" checked={showPatterns} onChange={(event) => setShowPatterns(event.target.checked)} /> PATTERNS</label>
      </div>
      <div className="chart-counts"><span className="candle-count">{payload?.candles.length.toLocaleString() ?? 0} CANDLES</span><span>{payload?.annotations.swings.length ?? 0} SWINGS</span><span>{payload?.annotations.breaks.length ?? 0} BREAKS</span><span>{payload?.annotations.patterns.length ?? 0} PATTERNS</span></div>
    </section>
    <section className="chart-surface">
      {error && <div className="chart-message error">{error}</div>}
      {loading && !payload && <div className="chart-message">LOADING CLOSED CANDLES</div>}
      <div ref={containerRef} className="chart-canvas" />
    </section>
    <footer className="chart-footer"><span>PRICE ONLY</span><span>{payload?.candles.length.toLocaleString() ?? 0} CLOSED CANDLES LOADED</span><span>DRAG LEFT FOR HISTORY</span>{saved && <span className="snapshot-saved">SAVED: {saved}</span>}</footer>
  </main>;
}
