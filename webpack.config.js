const path = require("path");

module.exports = {
  entry: {
    codelist: "./static/src/js/codelist.js",
    forest: "./static/src/js/forest.js",
  },
  output: {
    path: path.resolve(__dirname, "static", "dist", "js"),
    filename: "[name].bundle.js",
  },
};
