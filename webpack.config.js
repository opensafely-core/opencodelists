const path = require("node:path");

module.exports = {
  entry: {
    builder: "./assets/src/scripts/builder/index.jsx",
    codelist: "./assets/src/scripts/codelist.js",
    tree: "./assets/src/scripts/tree/index.jsx",
  },
  output: {
    path: path.resolve(__dirname, "assets", "dist", "js"),
    filename: "[name].bundle.js",
  },
  resolve: {
    extensions: [".js", ".jsx"],
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
