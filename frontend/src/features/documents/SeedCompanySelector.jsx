import { useState } from 'react'
import { Building2, Check } from 'lucide-react'

// Pre-defined seed companies for quick selection instead of manual upload.
// These can be expanded or fetched from backend later.
const SEED_COMPANIES = [
  { id: 'apple', name: 'Apple Inc.', ticker: 'AAPL' },
  { id: 'tesla', name: 'Tesla Inc.', ticker: 'TSLA' },
  { id: 'microsoft', name: 'Microsoft Corp.', ticker: 'MSFT' },
  { id: 'google', name: 'Alphabet Inc.', ticker: 'GOOGL' },
  { id: 'amazon', name: 'Amazon.com Inc.', ticker: 'AMZN' },
  { id: 'meta', name: 'Meta Platforms Inc.', ticker: 'META' },
]

function SeedCompanySelector({ selected, onSelect }) {
  return (
    <div>
      <h3 className="text-sm font-semibold text-gray-700 mb-3">Or pick a company</h3>
      <div className="grid grid-cols-2 gap-2">
        {SEED_COMPANIES.map((company) => {
          const isSelected = selected?.id === company.id
          return (
            <button
              key={company.id}
              onClick={() => onSelect(isSelected ? null : company)}
              className={`flex items-center gap-2.5 px-3 py-2.5 rounded-lg border text-sm text-left transition-colors ${
                isSelected
                  ? 'border-blue-500 bg-blue-50 text-blue-700'
                  : 'border-gray-200 bg-white text-gray-700 hover:border-gray-300 hover:bg-gray-50'
              }`}
            >
              <Building2 size={16} className={isSelected ? 'text-blue-500' : 'text-gray-400'} />
              <div className="flex-1 min-w-0">
                <p className="font-medium truncate">{company.name}</p>
                <p className="text-xs text-gray-400">{company.ticker}</p>
              </div>
              {isSelected && <Check size={14} className="text-blue-500 flex-shrink-0" />}
            </button>
          )
        })}
      </div>
    </div>
  )
}

export default SeedCompanySelector
