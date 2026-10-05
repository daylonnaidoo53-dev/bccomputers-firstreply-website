/**
 * BCComputers First-Reply Website — Quote Form Handler
 * Validates inbound lead fields and writes to Firestore 'leads' collection.
 */

import { db, isFirebaseConfigured } from './firebase-config.js';
import { collection, addDoc, serverTimestamp } from 'https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore.js';

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('quote-form');
  const statusBox = document.getElementById('form-status');
  const submitBtn = document.getElementById('submit-btn');

  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    // Clear previous status
    statusBox.className = 'form-status';
    statusBox.textContent = '';
    statusBox.style.display = 'none';

    // Extract values
    const businessName = form.businessName.value.trim();
    const contactName = form.contactName.value.trim();
    const phone = form.phone.value.trim();
    const email = form.email.value.trim();
    const area = form.area.value.trim() || 'Paarl';
    const tier = form.tier.value;
    const notes = form.notes.value.trim();

    // Collect selected add-ons
    const addons = [];
    form.querySelectorAll('input[name="addons"]:checked').forEach((cb) => {
      addons.push(cb.value);
    });

    // Validation
    if (!businessName) {
      showError('Please enter your business name.');
      form.businessName.focus();
      return;
    }

    if (!contactName) {
      showError('Please enter your contact name.');
      form.contactName.focus();
      return;
    }

    const cleanPhone = phone.replace(/[^0-9+]/g, '');
    if (!cleanPhone || cleanPhone.length < 10) {
      showError('Please enter a valid phone or WhatsApp number (minimum 10 digits).');
      form.phone.focus();
      return;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!email || !emailRegex.test(email)) {
      showError('Please enter a valid email address.');
      form.email.focus();
      return;
    }

    if (!tier) {
      showError('Please select a system tier.');
      form.tier.focus();
      return;
    }

    // Set UI to loading state
    const originalBtnText = submitBtn.innerHTML;
    submitBtn.disabled = true;
    submitBtn.innerHTML = `
      <span class="spinner" aria-hidden="true"></span>
      Submitting enquiry...
    `;

    const leadData = {
      businessName,
      contactName,
      phone: cleanPhone,
      email,
      area,
      tier,
      addons,
      notes,
      status: 'new',
      createdAt: new Date().toISOString()
    };

    // Build pre-filled WhatsApp link for direct instant contact
    const waText = encodeURIComponent(
      `Hi Daylon, I submitted an enquiry for the BCComputers First-Reply System.\n` +
      `• Business: ${businessName}\n` +
      `• Name: ${contactName}\n` +
      `• Tier: ${tier}\n` +
      `• Phone: ${cleanPhone}\n` +
      `• Area: ${area}`
    );
    const waLink = `https://wa.me/27832542999?text=${waText}`;

    try {
      if (isFirebaseConfigured() && db) {
        // Write to Firestore 'leads' collection
        await addDoc(collection(db, 'leads'), {
          ...leadData,
          serverTimestamp: serverTimestamp()
        });

        showSuccess(
          `Thank you, ${contactName}! Your enquiry has been received and logged into our system. ` +
          `Daylon will review your details and contact you within our 2-minute SLA.`,
          waLink
        );
        form.reset();
      } else {
        // Demo mode / Firestore not configured yet
        console.info('Firestore credentials pending. Displaying demo confirmation with direct WhatsApp handover.');
        showSuccess(
          `Thank you, ${contactName}! Your enquiry is ready. Click below to confirm directly with Daylon on WhatsApp right now.`,
          waLink
        );
        form.reset();
      }
    } catch (err) {
      console.error('Firestore submission error:', err);
      // Fallback: Gracefully ensure lead is not lost by routing directly to WhatsApp
      showSuccess(
        `Thank you, ${contactName}! To ensure zero delay, click below to message your enquiry straight to Daylon on WhatsApp.`,
        waLink
      );
    } finally {
      submitBtn.disabled = false;
      submitBtn.innerHTML = originalBtnText;
    }
  });

  function showError(msg) {
    statusBox.className = 'form-status error';
    statusBox.textContent = msg;
    statusBox.style.display = 'block';
  }

  function showSuccess(msg, waUrl) {
    statusBox.className = 'form-status success';
    statusBox.innerHTML = `
      <div class="status-content">
        <p><strong>✓ Received:</strong> ${msg}</p>
        <a href="${waUrl}" target="_blank" rel="noopener noreferrer" class="btn btn-whatsapp-direct">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
            <path d="M.057 24l1.687-6.163c-1.041-1.804-1.588-3.849-1.587-5.946.003-6.556 5.338-11.891 11.893-11.891 3.181.001 6.167 1.24 8.413 3.488 2.245 2.248 3.481 5.236 3.48 8.414-.003 6.557-5.338 11.892-11.893 11.892-1.99-.001-3.951-.5-5.688-1.448l-6.305 1.654zm6.597-3.807c1.676.995 3.276 1.591 5.392 1.592 5.448 0 9.886-4.434 9.889-9.885.002-5.462-4.415-9.89-9.881-9.892-5.452 0-9.887 4.434-9.889 9.884-.001 2.225.651 3.891 1.746 5.634l-.999 3.648 3.742-.981zm11.387-5.464c-.074-.124-.272-.198-.57-.347-.297-.149-1.758-.868-2.031-.967-.272-.099-.47-.149-.669.149-.198.297-.768.967-.941 1.165-.173.198-.347.223-.644.074-.297-.149-1.255-.462-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.297-.347.446-.521.151-.172.2-.296.3-.495.099-.198.05-.372-.025-.521-.075-.148-.669-1.611-.916-2.206-.242-.579-.487-.501-.669-.51l-.57-.01c-.198 0-.52.074-.792.372s-1.04 1.016-1.04 2.479 1.065 2.876 1.213 3.074c.149.198 2.095 3.2 5.076 4.487.709.306 1.263.489 1.694.626.712.226 1.36.194 1.872.118.571-.085 1.758-.719 2.006-1.413.248-.695.248-1.29.173-1.414z"/>
          </svg>
          Chat with Daylon on WhatsApp Now
        </a>
      </div>
    `;
    statusBox.style.display = 'block';
  }
});
