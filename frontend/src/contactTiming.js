import dayjs from 'dayjs';
import timezone from 'dayjs/plugin/timezone';
import utc from 'dayjs/plugin/utc';
import countryTimezones from './countryTimezones.js';

dayjs.extend(timezone);
dayjs.extend(utc);

class ContactTimingIntelligence {
  constructor() {
    this.selectedCountry = null;
    this.businessType = 'General';
    this.updateInterval = null;
    this.init();
  }

  init() {
    this.setupUI();
    this.bindEvents();
  }

  setupUI() {
    const timingPanel = document.createElement('div');
    timingPanel.id = 'contact-timing-panel';
    timingPanel.className = 'hidden bg-white rounded-lg shadow-lg p-6 mt-4';
    
    timingPanel.innerHTML = `
      <h3 class="text-lg font-semibold mb-4">Contact Timing Intelligence</h3>
      
      <div id="time-info" class="mb-6">
        <div class="flex items-center justify-between mb-2">
          <span class="text-sm text-gray-600">Current Time:</span>
          <span id="local-time" class="font-mono">--</span>
        </div>
        <div class="flex items-center justify-between">
          <span class="text-sm text-gray-600">Your Time (India):</span>
          <span id="ist-time" class="font-mono">--</span>
        </div>
      </div>

      <div id="best-time" class="mb-6">
        <h4 class="font-medium mb-2">🟢 Best Time to Contact (IST):</h4>
        <p id="best-time-window" class="text-sm">--</p>
        <p id="avoid-time-window" class="text-sm text-red-600 mt-1">⚠️ Avoid: --</p>
      </div>

      <div id="status-indicator" class="mb-6 p-4 bg-green-50 rounded border border-green-200">
        <div class="flex items-center">
          <div class="w-3 h-3 bg-green-400 rounded-full mr-3"></div>
          <div>
            <p id="status-text" class="font-medium">Perfect time to contact clients NOW</p>
            <p id="wait-time" class="text-sm text-gray-600 mt-1">--</p>
          </div>
        </div>
      </div>

      <div id="business-type" class="mb-6">
        <label class="block text-sm font-medium mb-2">Business Type:</label>
        <select id="business-type-select" class="w-full px-3 py-2 border rounded-md">
          <option value="General">General</option>
          <option value="Food & Beverage">Food & Beverage</option>
          <option value="Healthcare">Healthcare</option>
          <option value="Retail">Retail</option>
        </select>
      </div>

      <div id="best-days" class="mb-6">
        <h4 class="font-medium mb-2">📅 Best Days:</h4>
        <p class="text-sm">Monday - Friday</p>
        <p class="text-sm text-red-600 mt-1">⚠️ Avoid: Sunday, Saturday</p>
      </div>
    `;

    const searchForm = document.querySelector('form');
    searchForm.parentNode.insertBefore(timingPanel, searchForm.nextSibling);
  }

  bindEvents() {
    const countrySelect = document.getElementById('country-select');
    const businessTypeSelect = document.getElementById('business-type-select');

    countrySelect.addEventListener('change', (e) => {
      this.selectedCountry = e.target.value;
      this.updateTimingInfo();
      this.showPanel();
    });

    businessTypeSelect.addEventListener('change', (e) => {
      this.businessType = e.target.value;
      this.updateTimingInfo();
    });
  }

  showPanel() {
    document.getElementById('contact-timing-panel').classList.remove('hidden');
  }

  updateTimingInfo() {
    if (!this.selectedCountry) return;

    clearInterval(this.updateInterval);
    this.updateTimeDisplay();
    this.updateInterval = setInterval(() => this.updateTimeDisplay(), 60000);
  }

  updateTimeDisplay() {
    const localTz = countryTimezones[this.selectedCountry];
    const nowLocal = dayjs().tz(localTz);
    const nowIst = dayjs().tz('Asia/Kolkata');

    this.updateTimeElements(nowLocal, nowIst);
    this.updateBestTimeWindow(nowLocal);
    this.updateStatusIndicator(nowIst);
  }

  updateTimeElements(localTime, istTime) {
    document.getElementById('local-time').textContent = localTime.format('h:mm A');
    document.getElementById('ist-time').textContent = istTime.format('h:mm A') + ' IST';
  }

  updateBestTimeWindow(localTime) {
    const localBusinessStart = localTime.hour(9).minute(0);
    const localBusinessEnd = localTime.hour(18).minute(0);

    const istBusinessStart = localBusinessStart.tz('Asia/Kolkata');
    const istBusinessEnd = localBusinessEnd.tz('Asia/Kolkata');

    const categoryTimes = {
      'General': { start: 19.5, end: 23.5 },
      'Food & Beverage': { start: 18.5, end: 21.5 },
      'Healthcare': { start: 15.5, end: 19.5 },
      'Retail': { start: 17.5, end: 21.5 }
    };

    const categoryTime = categoryTimes[this.businessType];
    const categoryStart = localTime.hour(Math.floor(categoryTime.start)).minute(Math.round((categoryTime.start % 1) * 60));
    const categoryEnd = localTime.hour(Math.floor(categoryTime.end)).minute(Math.round((categoryTime.end % 1) * 60));

    const categoryStartIst = categoryStart.tz('Asia/Kolkata');
    const categoryEndIst = categoryEnd.tz('Asia/Kolkata');

    document.getElementById('best-time-window').textContent = 
      `${categoryStartIst.format('h:mm A')} - ${categoryEndIst.format('h:mm A')}`;

    const avoidStart = categoryStartIst.clone().subtract(2, 'hour');
    const avoidEnd = categoryStartIst.clone().subtract(6, 'hour');
    document.getElementById('avoid-time-window').textContent = 
      `⚠️ Avoid: ${avoidStart.format('h:mm A')} - ${avoidEnd.format('h:mm A')} IST`;
  }

  updateStatusIndicator(istTime) {
    const categoryTimes = {
      'General': { start: 19.5, end: 23.5 },
      'Food & Beverage': { start: 18.5, end: 21.5 },
      'Healthcare': { start: 15.5, end: 19.5 },
      'Retail': { start: 17.5, end: 21.5 }
    };

    const categoryTime = categoryTimes[this.businessType];
    const categoryStart = istTime.clone().hour(Math.floor(categoryTime.start)).minute(Math.round((categoryTime.start % 1) * 60));
    const categoryEnd = istTime.clone().hour(Math.floor(categoryTime.end)).minute(Math.round((categoryTime.end % 1) * 60));

    const statusPanel = document.getElementById('status-indicator');
    const statusText = document.getElementById('status-text');
    const waitTime = document.getElementById('wait-time');

    if (istTime.isBetween(categoryStart, categoryEnd)) {
      statusPanel.className = 'mb-6 p-4 bg-green-50 rounded border border-green-200';
      statusText.textContent = `Perfect time to contact ${this.selectedCountry} clients NOW`;
      waitTime.textContent = '--';
    } else {
      statusPanel.className = 'mb-6 p-4 bg-red-50 rounded border border-red-200';
      statusText.textContent = `Not the right time to contact ${this.selectedCountry} clients`;

      let nextWindow;
      if (istTime.isBefore(categoryStart)) {
        nextWindow = categoryStart;
      } else {
        nextWindow = categoryStart.add(1, 'day');
      }

      const diff = nextWindow.diff(istTime, 'minute');
      const hours = Math.floor(diff / 60);
      const minutes = diff % 60;

      waitTime.textContent = `Wait: ${hours} hours ${minutes} minutes`;
    }
  }
}

export default ContactTimingIntelligence;