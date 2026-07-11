"""从 Seller Central 各页面提取结构化数据。"""
from __future__ import annotations

import re
from typing import Any


EXTRACT_PERFORMANCE_TABLE_JS = """
() => {
  const money = (value) => {
    const match = String(value || '').match(/([\\d,]+(?:\\.\\d+)?)/);
    if (!match) return '';
    const num = parseFloat(match[1].replace(/,/g, ''));
    return Number.isFinite(num) ? num.toFixed(2) : '';
  };
  const percent = (value) => {
    const match = String(value || '').match(/([\\d.]+)\\s*%/);
    return match ? match[1] : '';
  };
  const STATUS_ONLY = /^(在售|停售|缺货|active|inactive|out of stock|–|-)$/i;
  const asinFromCell = (td, text) => {
    const href = td?.querySelector?.('a')?.href || '';
    const blob = `${href} ${text || ''}`;
    const match = blob.match(/\\b([A-Z0-9]{10})\\b/i);
    if (!match) return '';
    const asin = match[1].toUpperCase();
    return /[0-9]/.test(asin) ? asin : '';
  };
  const titleFromCell = (td) => {
    if (!td) return '';
    const link = td.querySelector('a');
    if (link) {
      const linked = (link.getAttribute('title') || link.innerText || '').trim();
      if (linked.length > 4 && !STATUS_ONLY.test(linked)) return linked;
    }
    const text = (td.innerText || '').trim();
    if (!text || STATUS_ONLY.test(text)) return '';
    return text;
  };
  const headerRules = [
    { key: 'product_name', pattern: /(title|商品名称|商品名|父商品|子商品|product name)/i },
    { key: 'asin', pattern: /asin/i },
    { key: 'sku', pattern: /sku/i },
    { key: 'revenue_30d', pattern: /(ordered product sales|已订购商品销售额|product sales(?!.*%))/i },
    { key: 'orders_30d', pattern: /(units ordered|已订购数量|订单量|ordered units)/i },
    { key: 'page_views', pattern: /(sessions|会话|page views)/i },
    { key: 'ad_spend_30d', pattern: /(spend|广告花费|广告支出|ad spend)/i },
    { key: 'acos', pattern: /acos/i },
    { key: 'tacos', pattern: /tacos/i },
    { key: 'conversion_rate', pattern: /(conversion|转化率|unit session)/i },
    { key: 'inventory', pattern: /(inventory|库存|available)/i },
  ];
  const scoreTable = (headers) => {
    const headerText = headers.join(' ').toLowerCase();
    let score = 0;
    if (/asin/i.test(headerText)) score += 4;
    if (/ordered product sales|已订购商品销售额/i.test(headerText)) score += 3;
    if (/units ordered|已订购数量|订单量/i.test(headerText)) score += 2;
    if (/sessions|会话/i.test(headerText)) score += 1;
    if (/status|状态/i.test(headerText) && !/asin/i.test(headerText)) score -= 3;
    if (/销售额|sales/i.test(headerText) && !/asin/i.test(headerText)) score -= 1;
    return score;
  };
  const rankedTables = Array.from(document.querySelectorAll('table'))
    .map((table) => {
      const headerCells = Array.from(table.querySelectorAll('thead th, tr th, tr:first-child td'));
      const headers = headerCells.map((cell) => (cell.innerText || '').trim()).filter(Boolean);
      return { table, headers, score: scoreTable(headers) };
    })
    .filter((item) => item.headers.length && item.score >= 3)
    .sort((a, b) => b.score - a.score);

  const rows = [];
  for (const { table, headers } of rankedTables) {
    const columnMap = {};
    headers.forEach((label, index) => {
      for (const rule of headerRules) {
        if (rule.pattern.test(label) && columnMap[rule.key] == null) {
          columnMap[rule.key] = index;
          break;
        }
      }
    });
    const bodyRows = table.querySelectorAll('tbody tr');
    bodyRows.forEach((tr, index) => {
      const tds = Array.from(tr.querySelectorAll('td'));
      const cells = tds.map((td) => (td.innerText || '').trim());
      if (!cells.length) return;
      let asin = '';
      let productName = '';
      tds.forEach((td) => {
        const fromCell = asinFromCell(td, td.innerText || '');
        if (fromCell) asin = fromCell;
        const title = titleFromCell(td);
        if (title.length > productName.length) productName = title;
      });
      if (columnMap.asin != null && tds[columnMap.asin]) {
        const fromCol = asinFromCell(tds[columnMap.asin], cells[columnMap.asin]);
        if (fromCol) asin = fromCol;
      }
      if (columnMap.product_name != null && tds[columnMap.product_name]) {
        const fromCol = titleFromCell(tds[columnMap.product_name]);
        if (fromCol) productName = fromCol;
      }
      if (!asin) return;
      if (!productName || STATUS_ONLY.test(productName)) productName = asin;
      const revenue = columnMap.revenue_30d != null ? money(cells[columnMap.revenue_30d]) : '';
      const spend = columnMap.ad_spend_30d != null ? money(cells[columnMap.ad_spend_30d]) : '';
      const acos = columnMap.acos != null ? percent(cells[columnMap.acos]) : '';
      rows.push({
        rank_no: index + 1,
        product_name: String(productName).slice(0, 180),
        asin,
        sku: columnMap.sku != null ? cells[columnMap.sku].slice(0, 80) : '',
        revenue_30d: revenue,
        orders_30d: columnMap.orders_30d != null ? money(cells[columnMap.orders_30d]) : '0',
        page_views: columnMap.page_views != null ? money(cells[columnMap.page_views]) : '0',
        ad_spend_30d: spend,
        acos,
        tacos: columnMap.tacos != null ? percent(cells[columnMap.tacos]) : '',
        conversion_rate: columnMap.conversion_rate != null ? percent(cells[columnMap.conversion_rate]) : '',
        inventory: columnMap.inventory != null ? money(cells[columnMap.inventory]) : '0',
        currency: 'USD',
      });
    });
    if (rows.length) break;
  }
  return rows.slice(0, 50);
}
"""

EXTRACT_BUSINESS_REPORT_JS = EXTRACT_PERFORMANCE_TABLE_JS
EXTRACT_PRODUCTS_JS = EXTRACT_BUSINESS_REPORT_JS

EXTRACT_INVENTORY_JS = """
() => {
  const STATUS_ONLY = /^(在售|停售|缺货|active|inactive|out of stock|–|-)$/i;
  const asinFrom = (text) => {
    const match = String(text || '').match(/\\b([A-Z0-9]{10})\\b/i);
    if (!match) return '';
    const asin = match[1].toUpperCase();
    return /[0-9]/.test(asin) ? asin : '';
  };
  const rows = [];
  const tables = Array.from(document.querySelectorAll('table'));
  for (const table of tables) {
    const header = (table.innerText || '').slice(0, 500);
    if (!/(asin|sku|title|商品|库存|inventory)/i.test(header)) continue;
    table.querySelectorAll('tbody tr').forEach((tr, index) => {
      const tds = Array.from(tr.querySelectorAll('td'));
      const text = (tr.innerText || '').trim();
      if (!text || text.length < 6) return;
      let asin = '';
      let productName = '';
      tds.forEach((td) => {
        const cell = (td.innerText || '').trim();
        const found = asinFrom(cell) || asinFrom(td.querySelector('a')?.href || '');
        if (found) asin = found;
        if (!productName && cell.length > 8 && !STATUS_ONLY.test(cell) && !asinFrom(cell)) {
          productName = cell;
        }
      });
      if (!asin) return;
      if (!productName || STATUS_ONLY.test(productName)) productName = asin;
      rows.push({
        rank_no: index + 1,
        product_name: productName.slice(0, 180),
        asin,
        sku: '',
        revenue_30d: '',
        orders_30d: '0',
        page_views: '0',
        ad_spend_30d: '',
        acos: '',
        tacos: '',
        conversion_rate: '',
        inventory: '0',
        currency: 'USD',
      });
    });
    if (rows.length) break;
  }
  return rows.slice(0, 50);
}
"""

EXTRACT_CATALOG_JS = """
() => {
  const STATUS_ONLY = /^(在售|停售|缺货|active|inactive|out of stock|–|-)$/i;
  const asinFromBlob = (blob) => {
    const text = String(blob || '');
    const fromUrl = text.match(/(?:\\/dp\\/|\\/gp\\/product\\/|asin=|\\/product\\/)([A-Z0-9]{10})/i);
    if (fromUrl) return fromUrl[1].toUpperCase();
    const plain = text.match(/\\b([A-Z0-9]{10})\\b/);
    if (plain && /[0-9]/.test(plain[1])) return plain[1].toUpperCase();
    return '';
  };
  const collectRoots = (node, out = []) => {
    if (!node) return out;
    out.push(node);
    if (node.shadowRoot) collectRoots(node.shadowRoot, out);
    node.querySelectorAll?.('*').forEach((el) => {
      if (el.shadowRoot) collectRoots(el.shadowRoot, out);
    });
    return out;
  };
  const roots = collectRoots(document);
  const rows = [];
  const seen = new Set();

  const pushRow = (asin, productName, extra = {}) => {
    if (!asin || seen.has(asin)) return;
    let name = String(productName || '').trim();
    if (!name || STATUS_ONLY.test(name)) name = asin;
    if (name.length < 3) return;
    seen.add(asin);
    rows.push({
      rank_no: rows.length + 1,
      product_name: name.slice(0, 180),
      asin,
      sku: extra.sku || '',
      revenue_30d: extra.revenue_30d || '',
      orders_30d: extra.orders_30d || '0',
      page_views: extra.page_views || '0',
      ad_spend_30d: extra.ad_spend_30d || '',
      acos: extra.acos || '',
      tacos: extra.tacos || '',
      conversion_rate: extra.conversion_rate || '',
      inventory: extra.inventory || '0',
      currency: 'USD',
    });
  };

  for (const root of roots) {
    for (const table of root.querySelectorAll('table')) {
      table.querySelectorAll('tbody tr, tr').forEach((tr) => {
        const tds = Array.from(tr.querySelectorAll('td, th'));
        if (!tds.length) return;
        let asin = '';
        let productName = '';
        tds.forEach((td) => {
          const cell = (td.innerText || '').trim();
          const href = td.querySelector('a')?.href || '';
          const found = asinFromBlob(`${href} ${cell}`);
          if (found) asin = found;
          if (!productName && cell.length > 6 && !STATUS_ONLY.test(cell) && !asinFromBlob(cell)) {
            productName = cell;
          }
          const link = td.querySelector('a');
          if (link) {
            const linked = (link.getAttribute('title') || link.innerText || '').trim();
            if (linked.length > productName.length && !STATUS_ONLY.test(linked)) {
              productName = linked;
            }
          }
        });
        if (asin) pushRow(asin, productName);
      });
    }
  }

  for (const root of roots) {
    for (const a of root.querySelectorAll('a[href]')) {
      const href = a.href || '';
      const asin = asinFromBlob(href);
      if (!asin) continue;
      const linked = (a.getAttribute('title') || a.innerText || '').trim();
      pushRow(asin, linked);
    }
  }

  return rows.slice(0, 50);
}
"""

EXTRACT_BR_GRID_JS = """
() => {
  const STATUS_ONLY = /^(在售|停售|缺货|active|inactive|out of stock|–|-)$/i;
  const money = (value) => {
    const match = String(value || '').match(/([\\d,]+(?:\\.\\d+)?)/);
    if (!match) return '';
    const num = parseFloat(match[1].replace(/,/g, ''));
    return Number.isFinite(num) ? num.toFixed(2) : '';
  };
  const asinFromBlob = (blob) => {
    const text = String(blob || '');
    const fromUrl = text.match(/(?:\\/dp\\/|\\/gp\\/product\\/|asin=|\\/product\\/)([A-Z0-9]{10})/i);
    if (fromUrl) return fromUrl[1].toUpperCase();
    const plain = text.match(/\\b([A-Z0-9]{10})\\b/);
    if (plain && /[0-9]/.test(plain[1])) return plain[1].toUpperCase();
    return '';
  };
  const collectRoots = (node, out = []) => {
    if (!node) return out;
    out.push(node);
    if (node.shadowRoot) collectRoots(node.shadowRoot, out);
    node.querySelectorAll?.('*').forEach((el) => {
      if (el.shadowRoot) collectRoots(el.shadowRoot, out);
    });
    return out;
  };
  const rows = [];
  const seen = new Set();
  const pushRow = (asin, productName, extra = {}) => {
    if (!asin || seen.has(asin)) return;
    let name = String(productName || '').trim();
    if (!name || STATUS_ONLY.test(name)) name = asin;
    seen.add(asin);
    rows.push({
      rank_no: rows.length + 1,
      product_name: name.slice(0, 180),
      asin,
      sku: extra.sku || '',
      revenue_30d: extra.revenue_30d || '',
      orders_30d: extra.orders_30d || '0',
      page_views: extra.page_views || '0',
      ad_spend_30d: extra.ad_spend_30d || '',
      acos: extra.acos || '',
      tacos: extra.tacos || '',
      conversion_rate: extra.conversion_rate || '',
      inventory: extra.inventory || '0',
      currency: 'USD',
    });
  };

  const parseRow = (tr) => {
    const tds = Array.from(tr.querySelectorAll('td, [role="gridcell"], th'));
    if (!tds.length) return;
    const cells = tds.map((td) => (td.innerText || '').trim());
    const blob = cells.join(' ');
    let asin = '';
    let productName = '';
    tds.forEach((td) => {
      const cell = (td.innerText || '').trim();
      const href = td.querySelector('a')?.href || '';
      const found = asinFromBlob(`${href} ${cell}`);
      if (found) asin = found;
      const linked = (td.querySelector('a')?.getAttribute('title') || td.querySelector('a')?.innerText || '').trim();
      if (linked.length > productName.length && !STATUS_ONLY.test(linked)) productName = linked;
      if (!productName && cell.length > 8 && !STATUS_ONLY.test(cell) && !asinFromBlob(cell)) productName = cell;
    });
    if (!asin) asin = asinFromBlob(blob);
    if (!asin) return;
    const nums = cells.map((cell) => money(cell)).filter(Boolean);
    pushRow(asin, productName, {
      revenue_30d: nums[0] || '',
      orders_30d: nums[1] || '0',
      page_views: nums[2] || '0',
    });
  };

  const roots = collectRoots(document);
  for (const root of roots) {
    root.querySelectorAll('table tbody tr, [role="row"]').forEach(parseRow);
  }
  return rows.slice(0, 50);
}
"""


EXTRACT_ORDERS_JS = """
() => {
  const rows = [];
  const tables = Array.from(document.querySelectorAll('table'));
  for (const table of tables) {
    const trs = table.querySelectorAll('tbody tr');
    trs.forEach((tr) => {
      const text = (tr.innerText || '').trim();
      if (!text) return;
      const orderMatch = text.match(/\\b(\\d{3}-\\d{7}-\\d{7})\\b/);
      if (!orderMatch) return;
      const asinMatch = text.match(/\\b(B0[A-Z0-9]{8,})\\b/i);
      const moneyMatch = text.match(/US\\$\\s*([\\d,]+(?:\\.\\d+)?)/i);
      const lines = text.split('\\n').map(s => s.trim()).filter(Boolean);
      const fulfillment = /自发货|MFN|Seller/i.test(text) ? 'fbm' : 'fba';
      let status = 'pending';
      if (/已发货|Shipped/i.test(text)) status = 'shipped';
      else if (/待揽收|Packed/i.test(text)) status = 'packed';
      rows.push({
        order_no: orderMatch[1],
        asin: asinMatch ? asinMatch[1] : '',
        sku: '',
        product_name: lines.find(l => l.length > 8 && !orderMatch[0].includes(l)) || '',
        quantity: 1,
        fulfillment_type: fulfillment,
        status,
        amount: moneyMatch ? moneyMatch[1] : '',
        currency: 'USD',
        ordered_at: '',
        ship_deadline: '',
        buyer_region: '',
      });
    });
    if (rows.length) break;
  }
  return rows.slice(0, 50);
}
"""


EXTRACT_MESSAGES_JS = """
() => {
  const rows = [];
  const nodes = Array.from(document.querySelectorAll('table tbody tr, [data-testid*="message"], .message-row'));
  nodes.forEach((node, index) => {
    const text = (node.innerText || '').trim();
    if (!text || text.length < 8) return;
    const orderMatch = text.match(/\\b(\\d{3}-\\d{7}-\\d{7})\\b/);
    const lines = text.split('\\n').map(s => s.trim()).filter(Boolean);
    const buyerName = lines[0] || 'Buyer';
    const subject = lines.find(l => l.length > 5 && l !== buyerName) || '买家消息';
    rows.push({
      id: `msg_${index + 1}`,
      buyer_name: buyerName.slice(0, 80),
      order_no: orderMatch ? orderMatch[1] : '',
      subject: subject.slice(0, 120),
      preview: text.slice(0, 220),
      received_at: '',
      sla_hours: 24,
      status: 'pending',
    });
  });
  return rows.slice(0, 30);
}
"""


EXTRACT_REVIEWS_JS = """
() => {
  const rows = [];
  const orderRe = /\\b\\d{3}-\\d{7}-\\d{7}\\b/;
  const dateRe = /\\d{4}[\\/-]\\d{1,2}[\\/-]\\d{1,2}/;
  const tables = Array.from(document.querySelectorAll('table'));

  const pushRow = (date, rating, orderNo, content, index) => {
    if (!rating || rating > 3 || !orderNo) return;
    rows.push({
      id: `rev_${orderNo}_${rating}`,
      order_no: orderNo,
      asin: '',
      product_name: '',
      rating,
      content: (content || '').slice(0, 300),
      reviewed_at: date || '',
      status: 'pending',
    });
  };

  for (const table of tables) {
    const headerText = (table.innerText || '').slice(0, 400);
    if (!/(日期|Date)/i.test(headerText) || !/(评级|Rating)/i.test(headerText)) continue;
    if (!/(订单|Order)/i.test(headerText)) continue;

    const trs = table.querySelectorAll('tbody tr');
    trs.forEach((tr, index) => {
      const cells = Array.from(tr.querySelectorAll('td')).map((c) => (c.innerText || '').trim());
      if (cells.length >= 3) {
        const date = (cells[0].match(dateRe) || [])[0] || cells[0];
        const rating = parseInt(cells[1], 10);
        const orderNo = (cells[2].match(orderRe) || [])[0] || '';
        const content = cells.length > 3 ? cells.slice(3).join(' ').trim() : '';
        pushRow(date, rating, orderNo, content, index);
        return;
      }

      const text = (tr.innerText || '').trim();
      if (!text) return;
      const orderMatch = text.match(orderRe);
      if (!orderMatch) return;
      const lines = text.split('\\n').map((s) => s.trim()).filter(Boolean);
      let rating = 0;
      let date = '';
      for (const line of lines) {
        if (/^[1-5]$/.test(line)) rating = parseInt(line, 10);
        if (dateRe.test(line)) date = (line.match(dateRe) || [])[0];
      }
      const content = lines
        .filter((l) => l !== String(rating) && l !== date && !orderRe.test(l) && l !== '选择一个')
        .join(' ')
        .trim();
      pushRow(date, rating, orderMatch[0], content, index);
    });
    if (rows.length) break;
  }
  return rows.slice(0, 30);
}
"""


def parse_reviews_from_text(text: str) -> list[dict[str, Any]]:
    """从反馈管理器页面纯文本解析 1–3 星差评（兜底）。"""
    body = text or ""
    if "反馈管理器" not in body and "feedback manager" not in body.lower():
        return []

    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    order_re = re.compile(r"\b(\d{3}-\d{7}-\d{7})\b")

    inline_re = re.compile(
        r"(\d{4}/\d{1,2}/\d{1,2})\s+([1-5])\s+(\d{3}-\d{7}-\d{7})",
    )
    for match in inline_re.finditer(body):
        date, rating_text, order_no = match.group(1), match.group(2), match.group(3)
        rating = int(rating_text)
        if rating > 3:
            continue
        dedupe = f"{order_no}:{rating}"
        if dedupe in seen:
            continue
        seen.add(dedupe)
        rows.append(
            {
                "id": f"rev_{order_no}_{rating}",
                "order_no": order_no,
                "asin": "",
                "product_name": "",
                "rating": rating,
                "content": "",
                "reviewed_at": date,
                "status": "pending",
            }
        )

    lines = [line.strip() for line in body.splitlines() if line.strip()]
    skip_tokens = {"选择一个", "", "操作", "评论", "评级", "订单编号", "日期"}

    index = 0
    while index < len(lines):
        date_match = re.match(r"(\d{4}/\d{1,2}/\d{1,2})$", lines[index])
        if not date_match or index + 2 >= len(lines):
            index += 1
            continue

        rating_match = re.match(r"^([1-5])$", lines[index + 1])
        order_match = order_re.search(lines[index + 2])
        if not rating_match or not order_match:
            index += 1
            continue

        rating = int(rating_match.group(1))
        order_no = order_match.group(1)
        if rating <= 3:
            content_parts: list[str] = []
            cursor = index + 3
            while cursor < len(lines):
                part = lines[cursor]
                if re.match(r"\d{4}/\d{1,2}/\d{1,2}$", part):
                    break
                if part in skip_tokens or order_re.fullmatch(part) or re.match(r"^[1-5]$", part):
                    cursor += 1
                    continue
                content_parts.append(part)
                cursor += 1
                if len(" ".join(content_parts)) >= 300:
                    break

            dedupe = f"{order_no}:{rating}"
            if dedupe not in seen:
                seen.add(dedupe)
                rows.append(
                    {
                        "id": f"rev_{order_no}_{rating}",
                        "order_no": order_no,
                        "asin": "",
                        "product_name": "",
                        "rating": rating,
                        "content": " ".join(content_parts)[:300],
                        "reviewed_at": date_match.group(1),
                        "status": "pending",
                    }
                )
        index += 1

    return rows[:30]


EXTRACT_COUPONS_JS = """
() => {
  const rows = [];
  const tables = Array.from(document.querySelectorAll('table'));
  const dateRe = /\\d{4}[\\/-]\\d{1,2}[\\/-]\\d{1,2}/;
  for (const table of tables) {
    const header = (table.innerText || '').slice(0, 500);
    if (!/(促销|Promotion|Coupon|优惠券|折扣|Discount)/i.test(header)) continue;
    table.querySelectorAll('tbody tr').forEach((tr, index) => {
      const text = (tr.innerText || '').trim();
      if (!text || text.length < 6) return;
      const lines = text.split('\\n').map((s) => s.trim()).filter(Boolean);
      const name = lines[0] || `Coupon ${index + 1}`;
      const discount = (text.match(/(\\d+\\s*%|US\\$\\s*[\\d.]+|\\$\\s*[\\d.]+)/) || [])[0] || '';
      const dates = text.match(dateRe) || [];
      let status = 'active';
      if (/过期|Expired|ended/i.test(text)) status = 'expired';
      else if (/即将|Expiring|ending soon/i.test(text)) status = 'expiring';
      else if (/异常|Error|invalid/i.test(text)) status = 'abnormal';
      rows.push({
        id: `cpn_${index + 1}`,
        name: name.slice(0, 160),
        discount: discount || '',
        start_at: dates[0] || '',
        end_at: dates[1] || dates[0] || '',
        status,
        redemptions: 0,
        budget: 0,
        note: '',
      });
    });
    if (rows.length) break;
  }
  return rows.slice(0, 30);
}
"""


EXTRACT_SHIPMENTS_JS = """
() => {
  const rows = [];
  const shipmentRe = /\\b(FBA[A-Z0-9]{8,}|STAR-[A-Z0-9-]+)\\b/i;
  const intRe = /\\b(\\d{1,6})\\b/g;
  const tables = Array.from(document.querySelectorAll('table'));
  for (const table of tables) {
    const header = (table.innerText || '').slice(0, 500);
    if (!/(货件|Shipment|Inbound|入库|FBA)/i.test(header)) continue;
    table.querySelectorAll('tbody tr').forEach((tr, index) => {
      const text = (tr.innerText || '').trim();
      const shipMatch = text.match(shipmentRe);
      if (!shipMatch) return;
      const lines = text.split('\\n').map((s) => s.trim()).filter(Boolean);
      const nums = [...text.matchAll(intRe)].map((m) => Number(m[1]));
      const expected = nums.length >= 2 ? nums[nums.length - 2] : (nums[0] || 0);
      const received = nums.length >= 2 ? nums[nums.length - 1] : expected;
      let status = 'in_transit';
      if (/已送达|Delivered|Closed|已完成|Receiving complete/i.test(text)) status = 'delivered';
      else if (/缺件|Shortage|Missing/i.test(text) || (expected > 0 && received < expected)) status = 'shortage';
      else if (/无货|no inventory|closed without/i.test(text)) status = 'closed_no_stock';
      const alertLevel = status === 'shortage' || status === 'closed_no_stock' ? 'danger' : 'normal';
      rows.push({
        id: `shp_${shipMatch[1]}`,
        shipment_id: shipMatch[1],
        product_name: lines.find((l) => l.length > 4 && !shipmentRe.test(l)) || '',
        sku: '',
        units_expected: expected,
        units_received: received,
        destination: '',
        status,
        alert_level: alertLevel,
        expected_at: '',
        note: '',
      });
    });
    if (rows.length) break;
  }
  return rows.slice(0, 40);
}
"""


EXTRACT_ADS_SUMMARY_JS = """
() => {
  const money = (raw) => {
    const match = String(raw || '').match(/([\\d,]+(?:\\.\\d+)?)/);
    if (!match) return '';
    const num = parseFloat(match[1].replace(/,/g, ''));
    return Number.isFinite(num) ? num.toFixed(2) : '';
  };
  const text = document.body.innerText || '';
  const spend = text.match(/(?:Spend|花费|支出|Cost)[\\s\\S]{0,80}?US\\$\\s*([\\d,]+(?:\\.\\d+)?)/i)
    || text.match(/US\\$\\s*([\\d,]+(?:\\.\\d+)?)[\\s\\S]{0,40}?(?:Spend|花费)/i);
  const sales = text.match(/(?:Ad sales|广告销售额|Sales attributed)[\\s\\S]{0,80}?US\\$\\s*([\\d,]+(?:\\.\\d+)?)/i);
  const acos = text.match(/ACOS[\\s\\S]{0,40}?([\\d.]+)\\s*%/i)
    || text.match(/([\\d.]+)\\s*%[\\s\\S]{0,20}?ACOS/i);
  return {
    ad_spend_30d: spend ? money(spend[1]) : '',
    ad_sales_30d: sales ? money(sales[1]) : '',
    acos: acos ? acos[1] : '',
  };
}
"""

EXTRACT_AD_CAMPAIGNS_JS = """
() => {
  const money = (value) => {
    const match = String(value || '').match(/([\\d,]+(?:\\.\\d+)?)/);
    if (!match) return '';
    const num = parseFloat(match[1].replace(/,/g, ''));
    return Number.isFinite(num) ? num.toFixed(2) : '';
  };
  const percent = (value) => {
    const match = String(value || '').match(/([\\d.]+)\\s*%/);
    return match ? match[1] : '';
  };
  const rows = [];
  const tables = Array.from(document.querySelectorAll('table'));
  for (const table of tables) {
    const headerCells = Array.from(table.querySelectorAll('thead th, tr th, tr:first-child td'));
    const headers = headerCells.map((c) => (c.innerText || '').trim()).filter(Boolean);
    if (!headers.length) continue;
    const headerText = headers.join(' ');
    if (!/(campaign|广告|spend|花费|acos|cost)/i.test(headerText)) continue;
    const columnMap = {};
    const rules = [
      { key: 'name', pattern: /(campaign|广告活动|name)/i },
      { key: 'asin', pattern: /asin/i },
      { key: 'sku', pattern: /sku/i },
      { key: 'spend', pattern: /(spend|花费|cost|支出)/i },
      { key: 'sales', pattern: /(sales|销售额|revenue)/i },
      { key: 'acos', pattern: /acos/i },
    ];
    headers.forEach((label, index) => {
      for (const rule of rules) {
        if (rule.pattern.test(label) && columnMap[rule.key] == null) {
          columnMap[rule.key] = index;
          break;
        }
      }
    });
    table.querySelectorAll('tbody tr').forEach((tr, index) => {
      const cells = Array.from(tr.querySelectorAll('td')).map((td) => (td.innerText || '').trim());
      if (!cells.length) return;
      const text = cells.join('\\n');
      if (text.length < 4) return;
      const asinMatch = text.match(/\\b(B0[A-Z0-9]{8,})\\b/i);
      const spend = columnMap.spend != null ? money(cells[columnMap.spend]) : '';
      const acos = columnMap.acos != null ? percent(cells[columnMap.acos]) : '';
      const name = columnMap.name != null ? cells[columnMap.name] : cells[0];
      if (!spend && !acos) return;
      rows.push({
        campaign_name: String(name || '').slice(0, 160),
        asin: columnMap.asin != null ? ((cells[columnMap.asin].match(/B0[A-Z0-9]{8,}/i) || [])[0] || '') : (asinMatch ? asinMatch[0] : ''),
        sku: columnMap.sku != null ? cells[columnMap.sku].slice(0, 80) : '',
        ad_spend_30d: spend,
        ad_sales_30d: columnMap.sales != null ? money(cells[columnMap.sales]) : '',
        acos,
      });
    });
    if (rows.length) break;
  }
  return rows.slice(0, 80);
}
"""


def parse_coupons_from_text(text: str) -> list[dict[str, Any]]:
    body = text or ""
    if (
        "促销" not in body
        and "Promotion" not in body
        and "Coupon" not in body
        and "优惠券" not in body
        and "coupon" not in body.lower()
    ):
        return []
    rows: list[dict[str, Any]] = []
    for index, line in enumerate(body.splitlines()):
        line = line.strip()
        if not line or len(line) < 4:
            continue
        discount = re.search(r"(\d+\s*%|US\$\s*[\d.]+|\$\s*[\d.]+)", line)
        if not discount:
            continue
        rows.append(
            {
                "id": f"cpn_txt_{index}",
                "name": line[:160],
                "discount": discount.group(1),
                "start_at": "",
                "end_at": "",
                "status": "expired" if "过期" in line or "Expired" in line else "active",
                "redemptions": 0,
                "budget": 0,
                "note": "",
            }
        )
    return rows[:30]


def parse_shipments_from_text(text: str) -> list[dict[str, Any]]:
    body = text or ""
    if not body.strip():
        return []
    if not re.search(r"(货件|Shipment|Inbound|入库|FBA|shipping\s*queue)", body, re.I):
        return []
    rows: list[dict[str, Any]] = []
    shipment_re = re.compile(r"\b(FBA[A-Z0-9]{8,}|STAR-[A-Z0-9-]+)\b", re.I)
    for match in shipment_re.finditer(body):
        sid = match.group(1)
        snippet = body[match.start() : match.start() + 200]
        nums = [int(n) for n in re.findall(r"\b(\d{1,6})\b", snippet)]
        expected = nums[-2] if len(nums) >= 2 else (nums[0] if nums else 0)
        received = nums[-1] if len(nums) >= 2 else expected
        status = "shortage" if expected > 0 and received < expected else "in_transit"
        if "已送达" in snippet or "Delivered" in snippet:
            status = "delivered"
        rows.append(
            {
                "id": f"shp_{sid}",
                "shipment_id": sid,
                "product_name": "",
                "sku": "",
                "units_expected": expected,
                "units_received": received,
                "destination": "",
                "status": status,
                "alert_level": "danger" if status == "shortage" else "normal",
                "expected_at": "",
                "note": "",
            }
        )
    dedup: dict[str, dict[str, Any]] = {}
    for row in rows:
        dedup[row["shipment_id"]] = row
    return list(dedup.values())[:40]


def parse_seller_news_from_text(text: str) -> list[dict[str, Any]]:
    body = text or ""
    items: list[dict[str, Any]] = []
    if "卖家新闻" not in body and "Seller news" not in body.lower():
        return items

    block_match = re.search(
        r"卖家新闻\s*(.*?)(?=全局快照|商品绩效|建议|隐藏式|$)",
        body,
        re.S,
    )
    block = block_match.group(1) if block_match else body
    lines = [line.strip() for line in block.splitlines() if line.strip()]
    skip = {"查看全部", "卖家新闻", "Seller news"}
    index = 0
    while index < len(lines):
        title = lines[index]
        if title in skip or re.match(r"^\d+$", title) or re.match(r"^\d+月", title):
            index += 1
            continue
        if len(title) < 8:
            index += 1
            continue
        date = ""
        if index + 1 < len(lines) and re.search(r"\d+月\s*\d+", lines[index + 1]):
            date = lines[index + 1]
        items.append(
            {
                "id": f"news_{len(items) + 1}",
                "title": title[:180],
                "summary": title[:220],
                "published_at": date,
                "status": "unread",
            }
        )
        index += 1
        if len(items) >= 10:
            break

    if not items and "业绩通知" in body:
        items.append(
            {
                "id": "news_perf",
                "title": "业绩通知",
                "summary": "请查看卖家平台业绩通知",
                "published_at": "",
                "status": "unread",
            }
        )
    return items


def parse_cases_from_text(text: str) -> list[dict[str, Any]]:
    body = text or ""
    cases: list[dict[str, Any]] = []
    match = re.search(r"管理问题日志[^\n]*?(\d+)", body)
    if match and int(match.group(1)) > 0:
        cases.append(
            {
                "id": "case_home_1",
                "case_id": "home_case_log",
                "title": "管理问题日志待处理",
                "status": "pending",
                "opened_at": "",
                "note": f"首页显示 {match.group(1)} 个问题需关注",
            }
        )
    news_match = re.search(r"业绩通知[^\n]*?(\d+)", body)
    if news_match:
        count = int(news_match.group(1))
        if count > 0:
            cases.append(
                {
                    "id": "news_home_1",
                    "case_id": "performance_notifications",
                    "title": "业绩通知",
                    "status": "pending",
                    "opened_at": "",
                    "note": f"近 120 天有 {count} 条业绩通知",
                }
            )
    return cases
