/**
 * Heating Oil Tank Card
 * A custom Lovelace card for visualizing oil tank levels
 */

class HeatingOilTankCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
  }

  static get properties() {
    return {
      hass: {},
      config: {},
    };
  }

  setConfig(config) {
    if (!config.entity) {
      throw new Error('Please define an entity (oil level percentage sensor)');
    }
    this.config = {
      title: config.title || 'Oil Tank',
      entity: config.entity,
      level_entity: config.level_entity,
      reading_entity: config.reading_entity,
      consumed_entity: config.consumed_entity,
      show_reading_input: config.show_reading_input !== false,
      warning_level: config.warning_level || 25,
      critical_level: config.critical_level || 10,
      ...config,
    };
  }

  set hass(hass) {
    this._hass = hass;
    this.render();
  }

  getCardSize() {
    return 4;
  }

  render() {
    if (!this._hass || !this.config) return;

    const entityId = this.config.entity;
    const state = this._hass.states[entityId];

    if (!state) {
      this.shadowRoot.innerHTML = `
        <ha-card>
          <div class="error">Entity not found: ${entityId}</div>
        </ha-card>
      `;
      return;
    }

    const percentage = parseFloat(state.state) || 0;
    const levelState = this.config.level_entity ? this._hass.states[this.config.level_entity] : null;
    const level = levelState ? parseFloat(levelState.state) : null;
    const capacity = state.attributes.tank_capacity || 1000;
    const lastReading = state.attributes.last_reading;
    const lastReadingDate = state.attributes.last_reading_date;
    const oilConsumed = state.attributes.oil_consumed;

    // Determine color based on level
    let fillColor = '#4CAF50'; // Green
    let statusText = 'Good';
    if (percentage <= this.config.critical_level) {
      fillColor = '#f44336'; // Red
      statusText = 'Critical - Order Now!';
    } else if (percentage <= this.config.warning_level) {
      fillColor = '#ff9800'; // Orange
      statusText = 'Low - Consider Ordering';
    }

    // Format the last reading date
    let formattedDate = 'Never';
    if (lastReadingDate) {
      const date = new Date(lastReadingDate);
      formattedDate = date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }

    this.shadowRoot.innerHTML = `
      <style>
        :host {
          --tank-fill-color: ${fillColor};
        }
        ha-card {
          padding: 16px;
          background: var(--ha-card-background, var(--card-background-color, white));
        }
        .card-header {
          font-size: 1.2em;
          font-weight: 500;
          margin-bottom: 16px;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        .status-badge {
          font-size: 0.7em;
          padding: 4px 8px;
          border-radius: 4px;
          background: ${fillColor};
          color: white;
        }
        .tank-container {
          display: flex;
          justify-content: center;
          align-items: flex-end;
          margin: 20px 0;
        }
        .tank {
          width: 120px;
          height: 200px;
          border: 4px solid var(--primary-text-color, #333);
          border-radius: 10px 10px 20px 20px;
          position: relative;
          overflow: hidden;
          background: var(--secondary-background-color, #f5f5f5);
        }
        .tank-fill {
          position: absolute;
          bottom: 0;
          left: 0;
          right: 0;
          background: linear-gradient(to top, ${fillColor}, ${this.lightenColor(fillColor, 20)});
          height: ${Math.min(100, Math.max(0, percentage))}%;
          transition: height 0.5s ease-in-out;
          border-radius: 0 0 16px 16px;
        }
        .tank-fill::before {
          content: '';
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          height: 10px;
          background: linear-gradient(to bottom, rgba(255,255,255,0.3), transparent);
        }
        .tank-marks {
          position: absolute;
          top: 0;
          right: -30px;
          height: 100%;
          display: flex;
          flex-direction: column;
          justify-content: space-between;
          font-size: 10px;
          color: var(--secondary-text-color, #666);
        }
        .percentage-display {
          position: absolute;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          font-size: 2em;
          font-weight: bold;
          color: ${percentage > 50 ? 'white' : 'var(--primary-text-color, #333)'};
          text-shadow: ${percentage > 50 ? '1px 1px 2px rgba(0,0,0,0.5)' : 'none'};
          z-index: 10;
        }
        .info-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 12px;
          margin-top: 16px;
        }
        .info-item {
          text-align: center;
          padding: 8px;
          background: var(--secondary-background-color, #f5f5f5);
          border-radius: 8px;
        }
        .info-label {
          font-size: 0.8em;
          color: var(--secondary-text-color, #666);
          margin-bottom: 4px;
        }
        .info-value {
          font-size: 1.1em;
          font-weight: 500;
          color: var(--primary-text-color, #333);
        }
        .reading-section {
          margin-top: 16px;
          padding-top: 16px;
          border-top: 1px solid var(--divider-color, #e0e0e0);
        }
        .reading-input-container {
          display: flex;
          gap: 8px;
          align-items: center;
          margin-top: 8px;
        }
        .reading-input {
          flex: 1;
          padding: 8px 12px;
          border: 1px solid var(--divider-color, #ccc);
          border-radius: 4px;
          font-size: 1em;
          background: var(--card-background-color, white);
          color: var(--primary-text-color, #333);
        }
        .reading-button {
          padding: 8px 16px;
          background: var(--primary-color, #03a9f4);
          color: white;
          border: none;
          border-radius: 4px;
          cursor: pointer;
          font-size: 0.9em;
        }
        .reading-button:hover {
          opacity: 0.9;
        }
        .last-reading {
          font-size: 0.85em;
          color: var(--secondary-text-color, #666);
          margin-top: 8px;
        }
        .error {
          color: var(--error-color, #db4437);
          padding: 16px;
        }
      </style>
      <ha-card>
        <div class="card-header">
          <span>${this.config.title}</span>
          <span class="status-badge">${statusText}</span>
        </div>

        <div class="tank-container">
          <div class="tank">
            <div class="tank-fill"></div>
            <div class="percentage-display">${percentage.toFixed(0)}%</div>
          </div>
          <div class="tank-marks">
            <span>100%</span>
            <span>75%</span>
            <span>50%</span>
            <span>25%</span>
            <span>0%</span>
          </div>
        </div>

        <div class="info-grid">
          <div class="info-item">
            <div class="info-label">Current Level</div>
            <div class="info-value">${level !== null ? level.toFixed(0) + ' L' : 'N/A'}</div>
          </div>
          <div class="info-item">
            <div class="info-label">Tank Capacity</div>
            <div class="info-value">${capacity} L</div>
          </div>
          <div class="info-item">
            <div class="info-label">Oil Consumed</div>
            <div class="info-value">${oilConsumed !== null && oilConsumed !== undefined ? oilConsumed.toFixed(1) + ' L' : 'N/A'}</div>
          </div>
          <div class="info-item">
            <div class="info-label">Last Reading</div>
            <div class="info-value">${lastReading !== null && lastReading !== undefined ? lastReading.toFixed(0) + ' L' : 'N/A'}</div>
          </div>
        </div>

        ${this.config.show_reading_input && this.config.reading_entity ? `
          <div class="reading-section">
            <div class="info-label">Update Tank Reading (enter actual level in litres)</div>
            <div class="reading-input-container">
              <input type="number" class="reading-input" id="reading-input"
                     min="0" max="${capacity}" step="1"
                     placeholder="Enter level in litres">
              <button class="reading-button" id="update-btn">Update</button>
            </div>
            <div class="last-reading">Last updated: ${formattedDate}</div>
          </div>
        ` : ''}
      </ha-card>
    `;

    // Add event listener for the update button
    if (this.config.show_reading_input && this.config.reading_entity) {
      const updateBtn = this.shadowRoot.getElementById('update-btn');
      const input = this.shadowRoot.getElementById('reading-input');

      if (updateBtn && input) {
        updateBtn.addEventListener('click', () => {
          const value = parseFloat(input.value);
          if (!isNaN(value) && value >= 0 && value <= capacity) {
            this._hass.callService('number', 'set_value', {
              entity_id: this.config.reading_entity,
              value: value,
            });
            input.value = '';
          }
        });

        input.addEventListener('keypress', (e) => {
          if (e.key === 'Enter') {
            updateBtn.click();
          }
        });
      }
    }
  }

  lightenColor(color, percent) {
    const num = parseInt(color.replace('#', ''), 16);
    const amt = Math.round(2.55 * percent);
    const R = (num >> 16) + amt;
    const G = ((num >> 8) & 0x00ff) + amt;
    const B = (num & 0x0000ff) + amt;
    return (
      '#' +
      (
        0x1000000 +
        (R < 255 ? (R < 1 ? 0 : R) : 255) * 0x10000 +
        (G < 255 ? (G < 1 ? 0 : G) : 255) * 0x100 +
        (B < 255 ? (B < 1 ? 0 : B) : 255)
      )
        .toString(16)
        .slice(1)
    );
  }

  static getConfigElement() {
    return document.createElement('heating-oil-tank-card-editor');
  }

  static getStubConfig() {
    return {
      entity: '',
      title: 'Oil Tank',
      warning_level: 25,
      critical_level: 10,
    };
  }
}

// Card Editor for visual configuration
class HeatingOilTankCardEditor extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
  }

  setConfig(config) {
    this._config = config;
    this.render();
  }

  set hass(hass) {
    this._hass = hass;
    this.render();
  }

  render() {
    if (!this._hass) return;

    this.shadowRoot.innerHTML = `
      <style>
        .form-group {
          margin-bottom: 16px;
        }
        label {
          display: block;
          margin-bottom: 4px;
          font-weight: 500;
        }
        input, select {
          width: 100%;
          padding: 8px;
          border: 1px solid var(--divider-color, #ccc);
          border-radius: 4px;
          box-sizing: border-box;
        }
        .hint {
          font-size: 0.8em;
          color: var(--secondary-text-color, #666);
          margin-top: 4px;
        }
      </style>
      <div class="form-group">
        <label>Title</label>
        <input type="text" id="title" value="${this._config.title || 'Oil Tank'}">
      </div>
      <div class="form-group">
        <label>Percentage Entity (required)</label>
        <input type="text" id="entity" value="${this._config.entity || ''}"
               placeholder="sensor.heating_oil_tank_oil_level_percentage">
        <div class="hint">The oil level percentage sensor</div>
      </div>
      <div class="form-group">
        <label>Level Entity (litres)</label>
        <input type="text" id="level_entity" value="${this._config.level_entity || ''}"
               placeholder="sensor.heating_oil_tank_oil_level">
        <div class="hint">The oil level sensor in litres</div>
      </div>
      <div class="form-group">
        <label>Reading Input Entity</label>
        <input type="text" id="reading_entity" value="${this._config.reading_entity || ''}"
               placeholder="number.heating_oil_tank_manual_oil_reading">
        <div class="hint">The number entity for manual readings</div>
      </div>
      <div class="form-group">
        <label>Warning Level (%)</label>
        <input type="number" id="warning_level" value="${this._config.warning_level || 25}" min="0" max="100">
      </div>
      <div class="form-group">
        <label>Critical Level (%)</label>
        <input type="number" id="critical_level" value="${this._config.critical_level || 10}" min="0" max="100">
      </div>
    `;

    // Add event listeners
    ['title', 'entity', 'level_entity', 'reading_entity', 'warning_level', 'critical_level'].forEach(id => {
      const input = this.shadowRoot.getElementById(id);
      if (input) {
        input.addEventListener('change', (e) => {
          const newConfig = { ...this._config };
          let value = e.target.value;
          if (id === 'warning_level' || id === 'critical_level') {
            value = parseInt(value, 10);
          }
          newConfig[id] = value;
          this._config = newConfig;
          this.dispatchEvent(new CustomEvent('config-changed', { detail: { config: newConfig } }));
        });
      }
    });
  }
}

customElements.define('heating-oil-tank-card', HeatingOilTankCard);
customElements.define('heating-oil-tank-card-editor', HeatingOilTankCardEditor);

window.customCards = window.customCards || [];
window.customCards.push({
  type: 'heating-oil-tank-card',
  name: 'Heating Oil Tank Card',
  description: 'A visual representation of your heating oil tank level',
  preview: true,
});

console.info(
  '%c HEATING-OIL-TANK-CARD %c v1.0.0 ',
  'color: white; background: #4CAF50; font-weight: bold;',
  'color: #4CAF50; background: white; font-weight: bold;'
);
