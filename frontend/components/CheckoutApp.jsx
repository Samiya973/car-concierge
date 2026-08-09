import React, { useState } from 'react';

export default function CheckoutApp({ payload }) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [successResult, setSuccessResult] = useState(null);
  // Add this right after: const [successResult, setSuccessResult] = useState(null);

  if (!payload || !payload.form_fields || !payload.payment_mock) {
      return (
          <div className="bg-white p-6 rounded-2xl border border-gray-200 mt-2 max-w-md w-full shadow-sm text-center">
              <p className="text-sm text-gray-500">Loading checkout...</p>
          </div>
      );
  }

  const handleMockPaymentSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData.entries());

    try {
      const response = await fetch(payload.submit_endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      const result = await response.json();
      setSuccessResult(result);
    } catch (error) {
      console.error("Payment failed", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (successResult) {
    return (
      <div className="bg-emerald-50 p-6 rounded-2xl border border-emerald-200 mt-2 max-w-md w-full shadow-sm">
        <h3 className="text-base font-bold text-emerald-900 mb-1">🎉 Transaction Confirmed</h3>
        <p className="text-xs text-emerald-700 mb-3">{successResult.message}</p>
        <div className="text-xs font-mono bg-emerald-100 text-emerald-900 p-2.5 rounded-lg">
          REF ID: {successResult.transaction_id}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white p-6 rounded-2xl border border-gray-200 mt-2 max-w-md w-full shadow-sm">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-base font-bold text-gray-900">{payload.title}</h3>
        <span className="text-xs font-semibold px-2.5 py-1 bg-amber-50 text-amber-800 rounded-full">Secure Checkout</span>
      </div>
      <p className="text-emerald-800 font-bold mb-4 text-lg font-mono">
        ₹{payload.amount.toLocaleString('en-IN')}
      </p>

      <form onSubmit={handleMockPaymentSubmit} className="space-y-3">
        {payload.form_fields.map((field) => (
          <div key={field.id}>
            <label className="block text-xs uppercase tracking-wider text-gray-500 mb-1 font-medium">
              {field.label}
            </label>
            <input
              type={field.type}
              name={field.id}
              required={field.required}
              placeholder={field.placeholder || ''}
              className="w-full bg-gray-50 rounded-xl p-2.5 text-sm text-gray-900 border border-gray-200 focus:border-emerald-700 focus:bg-white outline-none transition-all"
            />
          </div>
        ))}

        <div className="pt-2">
          <p className="text-xs text-gray-500 mb-2 font-medium">{payload.payment_mock.disclaimer}</p>
          <div className="grid grid-cols-2 gap-2">
            {payload.payment_mock.methods.map((method) => (
              <label key={method} className="cursor-pointer">
                <input type="radio" name="payment_method" value={method} className="peer sr-only" defaultChecked={method === 'Credit Card'} />
                <div className="text-center px-3 py-2 rounded-xl text-xs bg-gray-50 text-gray-600 peer-checked:bg-emerald-900 peer-checked:text-white border border-gray-200 peer-checked:border-emerald-900 transition-all font-medium">
                  {method}
                </div>
              </label>
            ))}
          </div>
        </div>

        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full bg-[#1F3D2B] hover:bg-[#16301F] disabled:bg-gray-400 text-white font-semibold py-3 px-4 rounded-xl mt-4 transition-all shadow-sm text-sm"
        >
          {isSubmitting ? 'Processing payment...' : 'Complete Secure Payment'}
        </button>
      </form>
    </div>
  );
}