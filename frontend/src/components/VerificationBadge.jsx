import React from 'react';
import { ShieldCheck, ShieldAlert, ShieldX, Cpu } from 'lucide-react';

/**
 * VerificationBadge renders the clinical verification status of a response.
 *
 * @param {Object} props
 * @param {string} props.status - "PASS" | "FAIL" | "UNKNOWN" | string
 * @param {number} [props.attempts=1] - Number of verification attempts
 * @param {boolean} [props.showAttempts=true] - Whether to display attempt counter
 * @param {string} [props.mode="live"] - "mock" | "live" | string
 */
export default function VerificationBadge({
  status,
  attempts = 1,
  showAttempts = true,
  mode = 'live',
}) {
  const normStatus = (status || '').toUpperCase();
  const isMock = mode === 'mock';

  // In mock development mode, never imply real evidence was verified
  if (isMock) {
    if (normStatus === 'PASS') {
      return (
        <span
          className="verification-badge mock"
          title="Development simulation: Verification simulated (mock mode)"
        >
          <Cpu size={14} />
          <span>Development Simulation</span>
          {showAttempts && (
            <span className="verification-attempts-tag">
              Verification simulated
            </span>
          )}
        </span>
      );
    }

    if (normStatus === 'FAIL') {
      return (
        <span
          className="verification-badge fail"
          title="Verification failed (simulated)"
        >
          <ShieldX size={14} />
          <span>Verification Failed</span>
          {showAttempts && (
            <span className="verification-attempts-tag">
              Simulated
            </span>
          )}
        </span>
      );
    }

    return (
      <span
        className="verification-badge unknown"
        title="Unable to verify (simulated)"
      >
        <ShieldAlert size={14} />
        <span>Unable to Verify</span>
        {showAttempts && (
          <span className="verification-attempts-tag">
            Simulated
          </span>
        )}
      </span>
    );
  }

  // Live Multi-Agent System Mode
  if (normStatus === 'PASS') {
    return (
      <span className="verification-badge pass" title="Clinically verified across evidence sources">
        <ShieldCheck size={14} />
        <span>Verified Evidence</span>
        {showAttempts && (
          <span className="verification-attempts-tag">
            {attempts} {attempts === 1 ? 'attempt' : 'attempts'}
          </span>
        )}
      </span>
    );
  }

  if (normStatus === 'FAIL') {
    return (
      <span className="verification-badge fail" title="Failed cross-verification or insufficient evidence">
        <ShieldX size={14} />
        <span>Verification Failed</span>
        {showAttempts && (
          <span className="verification-attempts-tag">
            {attempts} {attempts === 1 ? 'attempt' : 'attempts'}
          </span>
        )}
      </span>
    );
  }

  return (
    <span className="verification-badge unknown" title="Unable to conclusively verify with current evidence">
      <ShieldAlert size={14} />
      <span>Unable to Verify</span>
      {showAttempts && (
        <span className="verification-attempts-tag">
          {attempts} {attempts === 1 ? 'attempt' : 'attempts'}
        </span>
      )}
    </span>
  );
}

