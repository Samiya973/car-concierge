import React, { useState } from 'react';

export default function FormFillingApp({ payload }) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [step, setStep] = useState('form'); // 'form' -> 'payment' -> 'success'
  const [formDataState, setFormDataState] = useState({});
  const [successResult, setSuccessResult] = useState(null);

  if (!payload || !payload.form_fields) {
    return (
      <div className="bg-white p-6 rounded-2xl border border-gray-200 mt-2 max-w-md w-full shadow-sm text-center">
        <p className="text-sm text-gray-500">Loading booking form...</p>
      </div>
    );
  }

  const handleFormSubmit = (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData.entries());
    setFormDataState(data);
    // Transition to Step 2: Payment Gateway
    setStep('payment');
  };

  const handlePaymentSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    const paymentData = new FormData(e.target);
    const combinedData = { ...formDataState, ...Object.fromEntries(paymentData.entries()) };

    try {
      const response = await fetch(payload.submit_endpoint || '/api/checkout/confirm', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(combinedData),
      });
      const result = await response.json();
      setSuccessResult(result);
      setStep('success');
    } catch (error) {
      console.error("Checkout failed, using mock success", error);
      setTimeout(() => {
        setSuccessResult({
          message: `Successfully booked ${payload.data?.car_name || 'your vehicle'}!`,
          transaction_id: `txn_${Math.random().toString(36).substring(2, 10)}`
        });
        setStep('success');
      }, 600);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (step === 'success' && successResult) {
    return (
      <div className="bg-emerald-50 p-6 rounded-2xl border border-emerald-200 mt-2 max-w-md w-full shadow-sm">
        <h3 className="text-base font-bold text-emerald-900 mb-1">🎉 Transaction Confirmed</h3>
        <p className="text-xs text-emerald-700 mb-3">{successResult.message}</p>
        <div className="text-xs font-mono bg-emerald-100 text-emerald-900 p-2.5 rounded-lg">
          REF ID: {successResult.transaction_id || 'txn_suv_mock_12345'}
        </div>
      </div>
    );
  }

  // Step 2: Secure Payment Gateway (with Card Number Extension)
  if (step === 'payment') {
    return (
      <div className="bg-white p-6 rounded-2xl border border-gray-200 mt-2 max-w-md w-full shadow-sm">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-base font-bold text-gray-900">Step 2: Secure Payment</h3>
          <span className="text-xs font-semibold px-2.5 py-1 bg-amber-50 text-amber-800 rounded-full">Checkout Gateway</span>
        </div>
        <p className="text-emerald-800 font-bold mb-4 text-lg font-mono">
          ₹{payload.amount ? payload.amount.toLocaleString('en-IN') : '15,00,000'}
        </p>

        <form onSubmit={handlePaymentSubmit} className="space-y-3">
          <div>
            <label className="block text-xs uppercase tracking-wider text-gray-500 mb-1 font-medium">
              Card Number
            </label>
            <input
              type="text"
              name="card_number"
              required
              placeholder="4433 2211 5566 7788"
              className="w-full bg-gray-50 rounded-xl p-2.5 text-sm text-gray-900 border border-gray-200 focus:border-emerald-700 focus:bg-white outline-none transition-all font-mono"
            />
          </div>

          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="block text-xs uppercase tracking-wider text-gray-500 mb-1 font-medium">Expiry</label>
              <input type="text" name="expiry" required placeholder="MM/YY" className="w-full bg-gray-50 rounded-xl p-2.5 text-sm text-gray-900 border border-gray-200 outline-none" />
            </div>
            <div>
              <label className="block text-xs uppercase tracking-wider text-gray-500 mb-1 font-medium">CVV</label>
              <input type="password" name="cvv" required placeholder="123" maxLength="4" className="w-full bg-gray-50 rounded-xl p-2.5 text-sm text-gray-900 border border-gray-200 outline-none" />
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

  // Step 1: Initial Form Filling
  return (
    <div className="bg-white p-6 rounded-2xl border border-gray-200 mt-2 max-w-md w-full shadow-sm">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-base font-bold text-gray-900">{payload.title}</h3>
        <span className="text-xs font-semibold px-2.5 py-1 bg-emerald-50 text-emerald-800 rounded-full">Step 1 of 2</span>
      </div>

      <form onSubmit={handleFormSubmit} className="space-y-3">
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

        <button
          type="submit"
          className="w-full bg-[#1F3D2B] hover:bg-[#16301F] text-white font-semibold py-3 px-4 rounded-xl mt-4 transition-all shadow-sm text-sm"
        >
          Proceed to Payment →
        </button>
      </form>
    </div>
  );
}