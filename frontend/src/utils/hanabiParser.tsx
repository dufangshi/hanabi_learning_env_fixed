// src/utils/hanabiParser.js


export function parseHanabiState(jsonData) {
    const { info } = jsonData;
    const fireworks = (info && info.fireworks) ? info.fireworks : {};
    return { fireworks };
  }
  