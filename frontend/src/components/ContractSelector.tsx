import { useEffect, useState } from 'react';
import type { Contract } from '../lib/types';
import { fetchContracts } from '../lib/api';

interface ContractSelectorProps {
  selectedContractId: string | null;
  onContractChange: (contractId: string | null) => void;
  disabled?: boolean;
}

export function ContractSelector({
  selectedContractId,
  onContractChange,
  disabled,
}: ContractSelectorProps) {
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchContracts()
      .then((data) => {
        setContracts(data);
        if (!selectedContractId && data.length > 0) {
          onContractChange(data[0].contract_id);
        }
      })
      .catch((err) => {
        setError(err.message);
      })
      .finally(() => {
        setLoading(false);
      });
  }, [selectedContractId, onContractChange]);

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <p className="text-sm text-gray-500">Cargando contratos...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-danger-50 border border-danger-200 rounded-lg p-4">
        <p className="text-sm text-danger-800">Error: {error}</p>
      </div>
    );
  }

  const selectedContract = contracts.find((c) => c.contract_id === selectedContractId);

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
      <label htmlFor="contract-select" className="block text-sm font-semibold text-gray-700 mb-2">
        Contrato de Salud
      </label>
      <select
        id="contract-select"
        value={selectedContractId || ''}
        onChange={(e) => onContractChange(e.target.value || null)}
        disabled={disabled}
        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 disabled:opacity-50"
      >
        {contracts.map((contract) => (
          <option key={contract.contract_id} value={contract.contract_id}>
            {contract.contract_name}
          </option>
        ))}
      </select>
      {selectedContract && (
        <p className="mt-2 text-xs text-gray-600">{selectedContract.description}</p>
      )}
    </div>
  );
}
