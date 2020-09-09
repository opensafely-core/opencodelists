const path = require("path");

module.exports = {
  entry: {
    builder: "./static/src/js/builder.jsx",
    codelist: "./static/src/js/codelist.js",
  },
  output: {
    path: path.resolve(__dirname, "static", "dist", "js"),
    filename: "[name].bundle.js",
  },
  resolve: {
    extensions: [".ts", ".tsx", ".js", ".jsx"],
  },
  module: {
    rules: [
      {
        test: /\.(t|j)sx?$/,
        use: { loader: "ts-loader" },
      },

      {
        enforce: "pre",
        test: /\.js$/,
        exclude: /node_modules/,
        loader: "source-map-loader",
      },
    ],
  },
  devtool: "source-map",
};
