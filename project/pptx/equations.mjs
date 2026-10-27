// LaTeX sources for every equation in the deck. Edit here, then run `node make_pptx.mjs`.
export const EQ = {
  // Slide 9: information time points and symbols
  t168: String.raw`\tau - 168\,\mathrm{h}`,
  t24: String.raw`\tau - 24\,\mathrm{h}`,
  t1: String.raw`\tau - 1\,\mathrm{h}`,
  wPrev: String.raw`W_{\tau-1\mathrm{h}}`,
  wTarget: String.raw`W_\tau`,
  yTarget: String.raw`y_\tau`,
  // Slide 10: Ridge objective
  ridge: String.raw`\min_{\mathbf{w},b}
\sum_{i=1}^{n}
\left(y_i-b-\mathbf{x}_i^\top\mathbf{w}\right)^2
+
\alpha\lVert\mathbf{w}\rVert_2^2`,
  // Slide 11: weather information comparison and ablation
  gain: String.raw`\mathrm{Gain}_{\mathrm{history}}
=
\mathrm{MAE}(\mathrm{E1})
-
\mathrm{MAE}(\mathrm{E2})`,
  gap: String.raw`\mathrm{Gap}_{\mathrm{oracle}}
=
\mathrm{MAE}(\mathrm{E2})
-
\mathrm{MAE}(\mathrm{E3})`,
  ablate: String.raw`\Delta\mathrm{MAE}_{\mathrm{remove}}(G)
=
\mathrm{MAE}(-G)
-
\mathrm{MAE}(\mathrm{Full\ E2})`,
  // Slide 12: evaluation metrics
  mae: String.raw`\mathrm{MAE}
=
\frac{1}{n}
\sum_{i=1}^{n}
\left|y_i-\hat{y}_i\right|`,
  rmse: String.raw`\mathrm{RMSE}
=
\sqrt{
\frac{1}{n}
\sum_{i=1}^{n}
\left(y_i-\hat{y}_i\right)^2
}`,
};
