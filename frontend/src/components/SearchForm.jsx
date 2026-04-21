import React, { useState } from "react";
import ContactTimingIntelligence from "../contactTiming.jsx";
import { useEffect } from "react";

function SearchForm({ onSearch, loading, loadingStage }) {
  const [showTiming, setShowTiming] = useState(false);
  const [selectedCountry, setSelectedCountry] = useState(null);
  const [businessType, setBusinessType] = useState('General');

  const handleSubmit = (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const query = {
      type: formData.get("type"),
      country: formData.get("country"),
      city: formData.get("city"),
    };
    setSelectedCountry(formData.get("country"));
    setBusinessType('General');
    onSearch(query);
  };

  return (
    <>
      <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3 sm:gap-6">
        <div>
          <label htmlFor="type" className="block text-sm font-medium text-slate-900 dark:text-white">
            Category
          </label>
          <select
            id="type"
            name="type"
            required
            className="mt-1 block w-full pl-3 pr-10 py-2 border border-slate-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm dark:bg-slate-700 dark:border-slate-600 dark:text-white dark:focus:ring-indigo-500"
          >
            <option value="">Select category</option>
            <option value="Restaurant">Restaurant</option>
            <option value="Hospital">Hospital</option>
            <option value="Retail Store">Retail Store</option>
            <option value="Hotel">Hotel</option>
            <option value="School">School</option>
          </select>
        </div>

        <div>
          <label htmlFor="country" className="block text-sm font-medium text-slate-900 dark:text-white">
            Country
          </label>
          <select
            id="country"
            name="country"
            required
            className="mt-1 block w-full pl-3 pr-10 py-2 border border-slate-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm dark:bg-slate-700 dark:border-slate-600 dark:text-white dark:focus:ring-indigo-500"
          >
            <option value="">Select country</option>
            <option value="United States">United States</option>
            <option value="India">India</option>
            <option value="United Kingdom">United Kingdom</option>
            <option value="Canada">Canada</option>
            <option value="Australia">Australia</option>
            <option value="Germany">Germany</option>
            <option value="France">France</option>
            <option value="Japan">Japan</option>
            <option value="China">China</option>
            <option value="Brazil">Brazil</option>
            <option value="Mexico">Mexico</option>
            <option value="South Africa">South Africa</option>
            <option value="Singapore">Singapore</option>
            <option value="United Arab Emirates">United Arab Emirates</option>
            <option value="Russia">Russia</option>
            <option value="Italy">Italy</option>
            <option value="Spain">Spain</option>
            <option value="South Korea">South Korea</option>
            <option value="Indonesia">Indonesia</option>
            <option value="Thailand">Thailand</option>
          </select>
        </div>

        <div>
          <label htmlFor="city" className="block text-sm font-medium text-slate-900 dark:text-white">
            City
          </label>
          <input
            type="text"
            id="city"
            name="city"
            required
            placeholder="Enter city"
            className="mt-1 block w-full pl-3 pr-10 py-2 border border-slate-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm dark:bg-slate-700 dark:border-slate-600 dark:text-white dark:focus:ring-indigo-500"
          />
        </div>
      </div>

      <div className="flex justify-end">
        <button
          type="submit"
          disabled={loading}
          className="inline-flex items-center justify-center gap-2 rounded-xl border border-indigo-200 bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white shadow-md shadow-indigo-500/20 transition-all duration-200 hover:-translate-y-0.5 hover:bg-indigo-700 disabled:cursor-not-allowed disabled:border-slate-200 disabled:bg-slate-300 disabled:shadow-none disabled:hover:translate-y-0 dark:border-indigo-500/30 dark:disabled:bg-slate-700"
        >
          {loading ? (
            <>
              <span className="h-4 w-4 animate-spin rounded-full border-2 border-indigo-300 border-t-indigo-600" />
              {loadingStage || "Searching"}
            </>
          ) : (
            "Search"
          )}
        </button>
      </div>
      </form>

      {showTiming && selectedCountry && (
        <ContactTimingIntelligence
          selectedCountry={selectedCountry}
          businessType={businessType}
          onBusinessTypeChange={setBusinessType}
        />
      )}
    </>
  );
}

export default SearchForm;