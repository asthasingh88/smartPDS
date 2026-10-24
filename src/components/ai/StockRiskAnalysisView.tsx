
import React, { useState } from 'react';
import { useApp } from '../../context/AppContext';
import {
  AlertTriangle,
  Droplets,
  Sparkles,
  Clock,
  TrendingUp,
  RefreshCw,
} from 'lucide-react';

interface DemandPrediction {
  commodity: string;
  predicted_demand_kg: number;
  unit: string;
  data_note: string;
}

export const StockRiskAnalysisView: React.FC = () => {
  const { batches } = useApp();

  const [commodity, setCommodity] = useState('wheat');
  const [demand, setDemand] = useState<DemandPrediction | null>(null);
  const [demandLoading, setDemandLoading] = useState(false);
  const [demandError, setDemandError] = useState('');

  const eligibleBatches = batches.filter(
    (b) => b.status === 'Eligible' && b.availableBags > 0
  );

  const age0to30 = eligibleBatches.filter((b) => b.stockAgeDays <= 30);
  const age31to60 = eligibleBatches.filter(
    (b) => b.stockAgeDays > 30 && b.stockAgeDays <= 60
  );
  const age61to90 = eligibleBatches.filter(
    (b) => b.stockAgeDays > 60 && b.stockAgeDays <= 90
  );
  const age90plus = eligibleBatches.filter((b) => b.stockAgeDays > 90);

  const highMoistureBatches = batches.filter(
    (b) => b.moisturePercentage >= 13
  );
  const quarantinedCount = batches.filter(
    (b) => b.status === 'Quarantined'
  ).length;
  const damagedCount = batches.filter(
    (b) => b.status === 'Damaged'
  ).length;

  const fetchDemandPrediction = async () => {
    setDemandLoading(true);
    setDemandError('');
    setDemand(null);

    const today = new Date();
    const startOfYear = new Date(today.getFullYear(), 0, 0);
    const dayOfYear = Math.floor(
      (today.getTime() - startOfYear.getTime()) / 86400000
    );

    try {
      const response = await fetch('/api/ml/demand', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          commodity,
          day_of_week: today.getDay(),
          day_of_month: today.getDate(),
          day_of_year: dayOfYear,

          // Demo inputs only; replace with historical dispatch data
          // before using predictions operationally.
          lag_1: 500,
          lag_7: 450,
          rolling_mean_7: 475,
        }),
      });

      const result = await response.json();

      if (!response.ok || !result.success) {
        throw new Error(result.error || 'Demand prediction failed.');
      }

      setDemand(result.prediction);
    } catch (error) {
      setDemandError(
        error instanceof Error
          ? error.message
          : 'Unable to connect to the ML service.'
      );
    } finally {
      setDemandLoading(false);
    }
  };

  const totalBags = (items: typeof eligibleBatches) =>
    items.reduce((sum, b) => sum + b.availableBags, 0);

  const riskCard =
    'p-4 bg-white dark:bg-[#151C28] rounded-xl border border-[#E7E2DF] dark:border-[#293445]';

  const bar = (
    label: string,
    items: typeof eligibleBatches,
    color: string
  ) => (
    <div key={label}>
      <div className="flex items-center justify-between text-xs font-semibold mb-1">
        <span>{label}</span>
        <span>
          {totalBags(items)} bags ({items.length} stacks)
        </span>
      </div>
      <div className="w-full bg-[#FAF7F2] dark:bg-[#111827] rounded-full h-2.5 overflow-hidden border border-[#E7E2DF] dark:border-[#293445]">
        <div
          className={`${color} h-full rounded-full`}
          style={{
            width: `${Math.min(
              100,
              (items.length / Math.max(1, eligibleBatches.length)) * 100
            )}%`,
          }}
        />
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* ML Demand Forecast */}
      <section className="p-5 bg-white dark:bg-[#151C28] rounded-xl border border-[#E7E2DF] dark:border-[#293445] space-y-4">
        <div className="flex items-center gap-2">
          <TrendingUp className="w-5 h-5 text-[#702D3B] dark:text-[#C4B5FD]" />
          <div>
            <h3 className="text-sm font-bold text-[#344054] dark:text-[#F1F5F9]">
              ML Demand Forecast
            </h3>
            <p className="text-xs text-[#707887] dark:text-[#A1AAB9] mt-1">
              Experimental prediction from the trained SmartPDS model.
            </p>
          </div>
        </div>

        <div className="flex flex-wrap gap-3 items-end">
          <label className="text-xs font-medium text-[#344054] dark:text-[#F1F5F9]">
            Commodity
            <select
              value={commodity}
              onChange={(e) => setCommodity(e.target.value)}
              className="block mt-1 p-2 rounded-lg border border-[#E7E2DF] dark:border-[#293445] dark:bg-[#111827]"
            >
              <option value="wheat">Wheat</option>
              <option value="rice">Rice</option>
            </select>
          </label>

          <button
            type="button"
            onClick={fetchDemandPrediction}
            disabled={demandLoading}
            className="px-4 py-2 rounded-lg bg-[#702D3B] hover:opacity-90 text-white text-sm font-semibold disabled:opacity-50 flex items-center gap-2"
          >
            <RefreshCw
              className={`w-4 h-4 ${demandLoading ? 'animate-spin' : ''}`}
            />
            {demandLoading ? 'Predicting...' : 'Predict Demand'}
          </button>
        </div>

        {demandError && (
          <p role="alert" className="text-sm text-red-600 dark:text-red-400">
            {demandError}
          </p>
        )}

        {demand && (
          <div className="p-4 rounded-lg bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-800">
            <p className="text-xs text-emerald-800 dark:text-emerald-300">
              Predicted demand — {demand.commodity}
            </p>
            <p className="text-2xl font-bold text-emerald-900 dark:text-emerald-200 mt-1">
              {demand.predicted_demand_kg.toLocaleString()} {demand.unit}
            </p>
            <p className="text-xs mt-2 text-emerald-800 dark:text-emerald-300">
              {demand.data_note}
            </p>
          </div>
        )}

        <p className="text-[11px] text-amber-700 dark:text-amber-300">
          Demo limitation: historical demand inputs are placeholders. This
          prediction is not validated for real-world allocation decisions.
        </p>
      </section>

      {/* Existing dashboard header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 bg-white dark:bg-[#151C28] rounded-xl border border-[#E7E2DF] dark:border-[#293445] shadow-xs">
        <div>
          <div className="flex items-center gap-2 flex-wrap">
            <span className="px-2 py-0.5 text-[11px] font-semibold bg-[#FAF2F4] dark:bg-[#3B1020] text-[#702D3B] dark:text-[#C4B5FD] rounded border border-[#702D3B]/20 uppercase tracking-wider">
              Predictive Intelligence
            </span>
            <span className="text-xs text-[#707887] dark:text-[#A1AAB9]">
              Grain Shelf-Life & Spoilage Prevention
            </span>
          </div>
          <h2 className="text-lg font-bold text-[#344054] dark:text-[#F1F5F9] mt-1">
            Depot Stock Risk & Degradation Horizon Analysis
          </h2>
          <p className="text-xs text-[#707887] dark:text-[#A1AAB9] mt-1">
            Stock ageing, moisture alerts and rotation-risk indicators.
          </p>
        </div>
        <span className="px-3 py-1.5 rounded-lg bg-[#FAF2F4] dark:bg-[#3B1020] border border-[#702D3B]/30 text-[#702D3B] dark:text-[#C4B5FD] text-xs font-semibold flex items-center gap-1.5">
          <Sparkles className="w-3.5 h-3.5" />
          Stock Risk Analysis
        </span>
      </div>

      {/* Stock risk cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className={riskCard}>
          <div className="flex items-center justify-between text-xs text-[#707887]">
            <span className="font-semibold text-[#344054] dark:text-[#F1F5F9]">
              Urgent Rotation Stacks
            </span>
            <Clock className="w-4 h-4 text-amber-600" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-amber-700 dark:text-amber-400">
              {age90plus.length}
            </span>
            <span className="text-xs">batches over 90 days</span>
          </div>
          <p className="text-xs text-[#707887] mt-1">
            {totalBags(age90plus)} bags in the oldest ageing bracket.
          </p>
        </div>

        <div className={riskCard}>
          <div className="flex items-center justify-between text-xs text-[#707887]">
            <span className="font-semibold text-[#344054] dark:text-[#F1F5F9]">
              Moisture Caution Watch
            </span>
            <Droplets className="w-4 h-4 text-sky-600" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-[#702D3B] dark:text-[#C4B5FD]">
              {highMoistureBatches.length}
            </span>
            <span className="text-xs">stacks at or above 13%</span>
          </div>
          <p className="text-xs text-[#707887] mt-1">
            Review high-moisture batches and follow local storage procedures.
          </p>
        </div>

        <div className={riskCard}>
          <div className="flex items-center justify-between text-xs text-[#707887]">
            <span className="font-semibold text-[#344054] dark:text-[#F1F5F9]">
              Quarantine / Damaged
            </span>
            <AlertTriangle className="w-4 h-4 text-rose-600" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-rose-700 dark:text-rose-400">
              {quarantinedCount + damagedCount}
            </span>
            <span className="text-xs">batches</span>
          </div>
          <p className="text-xs text-[#707887] mt-1">
            Confirm stock status before any allocation.
          </p>
        </div>
      </div>

      {/* Stock ageing analysis */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="p-5 bg-white dark:bg-[#151C28] rounded-xl border border-[#E7E2DF] dark:border-[#293445] space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-[#E7E2DF] dark:border-[#293445]">
            <h3 className="text-sm font-bold text-[#344054] dark:text-[#F1F5F9]">
              Grain Ageing Horizon Distribution
            </h3>
            <Clock className="w-4 h-4 text-[#707887]" />
          </div>

          <div className="space-y-4">
            {bar('Fresh Stock (0–30 days)', age0to30, 'bg-emerald-500')}
            {bar('Standard Maturing (31–60 days)', age31to60, 'bg-sky-500')}
            {bar('Ageing Priority (61–90 days)', age61to90, 'bg-amber-500')}
            {bar('Critical Rotation (>90 days)', age90plus, 'bg-rose-700')}
          </div>
        </div>

        <div className="p-5 bg-white dark:bg-[#151C28] rounded-xl border border-[#E7E2DF] dark:border-[#293445] space-y-4">
          <div className="flex items-center gap-2 pb-3 border-b border-[#E7E2DF] dark:border-[#293445]">
            <AlertTriangle className="w-4 h-4 text-amber-600" />
            <h3 className="text-sm font-bold text-[#344054] dark:text-[#F1F5F9]">
              Stock Review Recommendations
            </h3>
          </div>

          {age90plus.length > 0 ? (
            <div className="p-3 rounded-lg bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800">
              <p className="font-bold text-sm text-amber-900 dark:text-amber-200">
                Priority rotation review
              </p>
              <p className="text-xs text-amber-800 dark:text-amber-300 mt-1">
                {age90plus.length} eligible batches are over 90 days old.
                Review their quality and dispatch priority.
              </p>
            </div>
          ) : (
            <p className="text-sm text-[#707887]">
              No eligible batches are currently over 90 days old.
            </p>
          )}

          {highMoistureBatches.length > 0 ? (
            <div className="p-3 rounded-lg bg-sky-50 dark:bg-sky-950/30 border border-sky-200 dark:border-sky-800">
              <p className="font-bold text-sm text-sky-900 dark:text-sky-200">
                Moisture inspection recommended
              </p>
              <p className="text-xs text-sky-800 dark:text-sky-300 mt-1">
                {highMoistureBatches.length} batches have recorded moisture
                at or above 13%. Verify measurements and follow storage SOPs.
              </p>
            </div>
          ) : (
            <p className="text-sm text-[#707887]">
              No batches meet the current moisture caution threshold.
            </p>
          )}

          {(quarantinedCount + damagedCount) > 0 && (
            <div className="p-3 rounded-lg bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-800">
              <p className="font-bold text-sm text-rose-900 dark:text-rose-200">
                Restricted stock
              </p>
              <p className="text-xs text-rose-800 dark:text-rose-300 mt-1">
                {quarantinedCount + damagedCount} batches are marked
                quarantined or damaged. Do not treat ML predictions as
                authorization to allocate restricted stock.
              </p>
            </div>
          )}

          <p className="text-[11px] text-[#707887]">
            These are stock-rule summaries from current app state, not outputs
            from the ML models.
          </p>
        </div>
      </div>
    </div>
  );
};
