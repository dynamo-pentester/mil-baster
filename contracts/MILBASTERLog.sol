// contracts/MILBASTERLog.sol
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/// @title MIL-BASTER Logging Contract (Minimal)
/// @notice Stores event hashes + small metadata for tamper-proof audit trail.
contract MILBASTERLog {
    struct LogEntry {
        uint256 ts;
        string eventHash;   // hex or base64 string of evidence hash
        uint8 anomalyType;  // application-specific code
        int16 trustDelta;   // signed delta applied
        address reporter;   // account that pushed the log
    }

    LogEntry[] public logs;
    event LogAdded(uint256 indexed index, string eventHash, uint8 anomalyType, int16 trustDelta, address indexed reporter, uint256 ts);

    /// @notice Add a new log entry. Keep gas small by storing short metadata.
    /// @param eventHash A short string representation (hex) of the evidence blob hash
    /// @param anomalyType small integer code for anomaly
    /// @param trustDelta small signed integer of trust delta
    function addLog(string calldata eventHash, uint8 anomalyType, int16 trustDelta) external {
        uint256 idx = logs.length;
        logs.push(LogEntry({
            ts: block.timestamp,
            eventHash: eventHash,
            anomalyType: anomalyType,
            trustDelta: trustDelta,
            reporter: msg.sender
        }));

        emit LogAdded(idx, eventHash, anomalyType, trustDelta, msg.sender, block.timestamp);
    }

    /// @notice Return number of logs stored
    function count() external view returns (uint256) {
        return logs.length;
    }

    /// @notice Get a log by index
    function getLog(uint256 index) external view returns (uint256 ts, string memory eventHash, uint8 anomalyType, int16 trustDelta, address reporter) {
        require(index < logs.length, "Index OOB");
        LogEntry storage e = logs[index];
        return (e.ts, e.eventHash, e.anomalyType, e.trustDelta, e.reporter);
    }
}
