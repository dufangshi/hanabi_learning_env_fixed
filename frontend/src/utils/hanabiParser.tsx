// src/utils/hanabiParser.js

/**
 * 解析 Hanabi 状态 JSON 对象，提取 fireworks 数据
 * @param {Object} jsonData - 接收到的 JSON 数据
 * @returns {Object} - 返回包含 fireworks 的对象
 */
export function parseHanabiState(jsonData) {
    const { info } = jsonData;
    const fireworks = (info && info.fireworks) ? info.fireworks : {};
    return { fireworks };
  }
  