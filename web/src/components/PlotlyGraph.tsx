/* eslint-disable @typescript-eslint/no-explicit-any */
"use client";

import dynamic from "next/dynamic";

// Only scatter and bar charts are used, so the partial Plotly bundle (about a third of the full one) is enough; it is
// loaded with the first chart, not with the page
const Plot = dynamic(async () => {
  const [{ default: createPlotlyComponent }, { default: Plotly }] = await Promise.all([
    import("react-plotly.js/factory"), import("plotly.js-basic-dist-min"),
  ]);
  return createPlotlyComponent(Plotly);
}, { ssr: false });

export default function PlotlyGraph({ data, layout, useResizeHandler = true, style = { width: "100%", height: "100%" }, onClick }: any) {
  return (
    <Plot
      data={data}
      layout={layout}
      useResizeHandler={useResizeHandler}
      style={style}
      config={{ responsive: true, displayModeBar: false }}
      onClick={onClick}
    />
  );
}
