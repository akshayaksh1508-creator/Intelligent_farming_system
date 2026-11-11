const { getDefaultConfig } = require("expo/metro-config");

const config = getDefaultConfig(__dirname);
// The on-device disease model (assets/model) ships inside the app.
config.resolver.assetExts.push("tflite");

module.exports = config;
