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
  module: {
    rules: [
      {
        test: /\.jsx$/,
        loader: "babel-loader",
      },
    ],
  },
};
