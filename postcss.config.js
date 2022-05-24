module.exports = {
  plugins: {
    "postcss-url": [
      {
        // Inline font files when working locally
        filter: (t) => {
          return /([a-zA-Z0-9\s_\\.\-\(\):])+(.woff|.woff2)$/i.test(t.url);
        },
        url: process.env.NODE_ENV !== "production" ? "inline" : null,
      },
    ],
  },
};
