// The partial Plotly bundle (scatter, bar and pie) has no types of its own; it is the same API as plotly.js
declare module "plotly.js-basic-dist-min" {
  import Plotly from "plotly.js";
  export default Plotly;
}
