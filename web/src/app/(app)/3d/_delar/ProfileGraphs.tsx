// The cross-section profile (V form) and the depth along a drawn path, under the results on the 3D page.
import PlotlyGraph from "@/components/PlotlyGraph";
import type { ThreeDAnalysisResult } from "@/lib/db";

export default function ProfileGraphs({ results, plotData, plotLayout }: {
  results: ThreeDAnalysisResult;
  plotData: unknown[];
  plotLayout: Record<string, unknown>;
}) {
  return (
    <div className="liquid-glass-island rounded-[36px] p-6 flex flex-col items-center justify-center relative shadow-sm border border-white/50 animate-in fade-in slide-in-from-bottom-8">
      
      <div className="w-full grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* V-form Graph */}
        <div>
          <h3 className="font-bold text-sm text-slate-700 mb-2">Tvärsnittsprofil (V-form)</h3>
          <div className="bg-white/80 rounded-2xl border border-white p-2 shadow-inner h-[300px]">
            <PlotlyGraph 
              data={plotData}
              layout={{ ...plotLayout, margin: { l: 40, r: 20, t: 20, b: 40 }, showlegend: false, paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)' }}
            />
          </div>
        </div>
        
        {/* Longitudinal Depth Profile */}
        {results.depth_profile && results.depth_profile.distances.length > 0 ? (
          <div>
            <h3 className="font-bold text-sm text-slate-700 mb-2">Topografisk Längdprofil (Djup längs banan)</h3>
            <div className="bg-white/80 rounded-2xl border border-white p-2 shadow-inner h-[300px]">
              <PlotlyGraph 
                data={[
                  { 
                    x: results.depth_profile.distances, 
                    y: results.depth_profile.depths, 
                    mode: 'lines+markers', 
                    line: { color: '#b7410e', shape: 'spline' }, 
                    marker: { size: 4 },
                    fill: 'tozeroy',
                    fillcolor: 'rgba(183, 65, 14, 0.1)',
                    name: 'Djup' 
                  }
                ]}
                layout={{
                  margin: { l: 40, r: 20, t: 20, b: 40 },
                  xaxis: { title: 'Avstånd längs spår (mm)' },
                  yaxis: { 
                    title: 'Spårdjup (mm)', 
                    autorange: 'reversed' // Reversed so deeper is lower
                  },
                  showlegend: false,
                  paper_bgcolor: 'rgba(0,0,0,0)',
                  plot_bgcolor: 'rgba(0,0,0,0)'
                }}
              />
            </div>
          </div>
        ) : (
          <div>
            <h3 className="font-bold text-sm text-slate-700 mb-2">Topografisk Längdprofil</h3>
            <div className="flex flex-col items-center justify-center h-[300px] bg-white/50 rounded-2xl border border-white/50 shadow-inner">
              <p className="text-slate-500 text-sm font-medium">Rita en bana (Path) på stenen</p>
              <p className="text-slate-400 text-xs mt-1">för att se spårdjupet längs skåran.</p>
            </div>
          </div>
        )}
      </div>
      
      <div className="mt-6 text-xs font-semibold text-slate-500 uppercase tracking-wide">
        💡 Tips: Dra en rektangel i graferna för att zooma &nbsp;&bull;&nbsp; Dubbelklicka för att återställa
      </div>
    </div>
  );
}
