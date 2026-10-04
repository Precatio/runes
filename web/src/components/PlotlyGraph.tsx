/* eslint-disable @typescript-eslint/no-explicit-any */
"use client";

import dynamic from "next/dynamic";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

export default function PlotlyGraph({ data, layout, useResizeHandler = true, style = { width: "100%", height: "100%" } }: any) {
  return (
    <Plot
      data={data}
      layout={layout}
      useResizeHandler={useResizeHandler}
      style={style}
      config={{ responsive: true, displayModeBar: false }}
    />
  );
}
