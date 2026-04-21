import dayjs from 'dayjs';
import timezone from 'dayjs/plugin/timezone';
import utc from 'dayjs/plugin/utc';
import countryTimezones from './countryTimezones.js';

dayjs.extend(timezone);
dayjs.extend(utc);

function ContactTimingIntelligence({ selectedCountry, businessType, onBusinessTypeChange }) {
  const [localTime, setLocalTime] = React.useState(null);
  const [istTime, setIstTime] = React.useState(null);
  const [bestTimeWindow, setBestTimeWindow] = React.useState('--');
  const [avoidTimeWindow, setAvoidTimeWindow] = React.useState('--');
  const [statusText, setStatusText] = React.useState('Perfect time to contact clients NOW');
  const [waitTime, setWaitTime] = React.useState('--');
  const [statusColor, setStatusColor] = React.useState('bg-green-50 border-green-200');
  const updateIntervalRef = React.useRef(null);

  React.useEffect(() => {
    return () => {
      if (updateIntervalRef.current) {
        clearInterval(updateIntervalRef.current);
      }
    };
  }, []);

  const updateTimeDisplay = () => {
    if (!selectedCountry) return;

    const localTz = countryTimezones[selectedCountry];
    const nowLocal = dayjs().tz(localTz);
    const nowIst = dayjs().tz('Asia/Kolkata');

    setLocalTime(nowLocal);
    setIstTime(nowIst);
    updateBestTimeWindow(nowLocal);
    updateStatusIndicator(nowIst);
  };

  const updateBestTimeWindow = (localTime) => {
    const categoryTimes = {
      'General': { start: 19.5, end: 23.5 },
      'Food & Beverage': { start: 18.5, end: 21.5 },
      'Healthcare': { start: 15.5, end: 19.5 },
      'Retail': { start: 17.5, end: 21.5 }
    };

    const categoryTime = categoryTimes[businessType];
    const categoryStart = localTime.hour(Math.floor(categoryTime.start)).minute(Math.round((categoryTime.start % 1) * 60));
    const categoryEnd = localTime.hour(Math.floor(categoryTime.end)).minute(Math.round((categoryTime.end % 1) * 60));

    const categoryStartIst = categoryStart.tz('Asia/Kolkata');
    const categoryEndIst = categoryEnd.tz('Asia/Kolkata');

    setBestTimeWindow(`${categoryStartIst.format('h:mm A')} - ${categoryEndIst.format('h:mm A')}`);

    const avoidStart = categoryStartIst.clone().subtract(2, 'hour');
    const avoidEnd = categoryStartIst.clone().subtract(6, 'hour');
    setAvoidTimeWindow(`⚠️ Avoid: ${avoidStart.format('h:mm A')} - ${avoidEnd.format('h:mm A')} IST`);
  };

  const updateStatusIndicator = (istTime) => {
    const categoryTimes = {
      'General': { start: 19.5, end: 23.5 },
      'Food & Beverage': { start: 18.5, end: 21.5 },
      'Healthcare': { start: 15.5, end: 19.5 },
      'Retail': { start: 17.5, end: 21.5 }
    };

    const categoryTime = categoryTimes[businessType];
    const categoryStart = istTime.clone().hour(Math.floor(categoryTime.start)).minute(Math.round((categoryTime.start % 1) * 60));
    const categoryEnd = istTime.clone().hour(Math.floor(categoryTime.end)).minute(Math.round((categoryTime.end % 1) * 60));

    if (istTime.isBetween(categoryStart, categoryEnd)) {
      setStatusColor('bg-green-50 border-green-200');
      setStatusText(`Perfect time to contact ${selectedCountry} clients NOW`);
      setWaitTime('--');
    } else {
      setStatusColor('bg-red-50 border-red-200');
      setStatusText(`Not the right time to contact ${selectedCountry} clients`);

      let nextWindow;
      if (istTime.isBefore(categoryStart)) {
        nextWindow = categoryStart;
      } else {
        nextWindow = categoryStart.add(1, 'day');
      }

      const diff = nextWindow.diff(istTime, 'minute');
      const hours = Math.floor(diff / 60);
      const minutes = diff % 60;

      setWaitTime(`Wait: ${hours} hours ${minutes} minutes`);
    }
  };

  React.useEffect(() => {
    if (selectedCountry) {
      updateTimeDisplay();
      updateIntervalRef.current = setInterval(updateTimeDisplay, 60000);
    }
    return () => {
      if (updateIntervalRef.current) {
        clearInterval(updateIntervalRef.current);
      }
    };
  }, [selectedCountry, businessType]);

  const handleBusinessTypeChange = (e) => {
    onBusinessTypeChange(e.target.value);
  };

  if (!selectedCountry) {
    return null;
  }

  return (
    <div id="contact-timing-panel" className="bg-white rounded-lg shadow-lg p-6 mt-4">
      <h3 className="text-lg font-semibold mb-4">Contact Timing Intelligence</h3>
      
      <div id="time-info" className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-gray-600">Current Time:</span>
          <span className="font-mono">{localTime ? localTime.format('h:mm A') : '--'}</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-600">Your Time (India):</span>
          <span className="font-mono">{istTime ? istTime.format('h:mm A') + ' IST' : '--'}</span>
        </div>
      </div>

      <div id="best-time" className="mb-6">
        <h4 className="font-medium mb-2">🟢 Best Time to Contact (IST):</h4>
        <p id="best-time-window" className="text-sm">{bestTimeWindow}</p>
        <p id="avoid-time-window" className="text-sm text-red-600 mt-1">{avoidTimeWindow}</p>
      </div>

      <div id="status-indicator" className={`mb-6 p-4 ${statusColor} rounded border`}>
        <div className="flex items-center">
          <div className={`w-3 h-3 bg-green-400 rounded-full mr-3 ${statusColor.includes('green') ? '' : 'bg-red-400'}`}></div>
          <div>
            <p id="status-text" className="font-medium">{statusText}</p>
            <p id="wait-time" className="text-sm text-gray-600 mt-1">{waitTime}</p>
          </div>
        </div>
      </div>

      <div id="business-type" className="mb-6">
        <label className="block text-sm font-medium mb-2">Business Type:</label>
        <select id="business-type-select" className="w-full px-3 py-2 border rounded-md" value={businessType} onChange={handleBusinessTypeChange}>
          <option value="General">General</option>
          <option value="Food & Beverage">Food & Beverage</option>
          <option value="Healthcare">Healthcare</option>
          <option value="Retail">Retail</option>
        </select>
      </div>

      <div id="best-days" className="mb-6">
        <h4 className="font-medium mb-2">📅 Best Days:</h4>
        <p className="text-sm">Monday - Friday</p>
        <p className="text-sm text-red-600 mt-1">⚠️ Avoid: Sunday, Saturday</p>
      </div>
    </div>
  );
}

export default ContactTimingIntelligence;
