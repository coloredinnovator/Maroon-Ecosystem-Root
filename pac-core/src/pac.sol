// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * Maroon PAC Core — Smart Contract Treasury (v4.0)
 * Codex §4.4: Decentralized governance and fund allocation.
 */

contract MaroonPAC {
    address public owner;
    
    struct Proposal {
        uint256 id;
        string title;
        string descriptionHash; // Points to IPFS/Merkle DAG in Truth-Teller
        uint256 amountRequested;
        address payable recipient;
        uint256 votesFor;
        uint256 votesAgainst;
        bool executed;
        uint256 endTime;
    }

    mapping(uint256 => Proposal) public proposals;
    uint256 public proposalCount;
    
    // Whitelisted voting members
    mapping(address => bool) public members;

    event ProposalCreated(uint256 id, string title, uint256 amountRequested);
    event Voted(uint256 proposalId, address voter, bool inFavor);
    event ProposalExecuted(uint256 id, address recipient, uint256 amount);
    event TelemetryEmitted(string eventType, string data);

    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }

    modifier onlyMember() {
        require(members[msg.sender], "Not a member");
        _;
    }

    constructor() {
        owner = msg.sender;
        members[msg.sender] = true; // Initial member
    }

    // Accept donations
    receive() external payable {}

    function addMember(address _member) external onlyOwner {
        members[_member] = true;
    }

    function removeMember(address _member) external onlyOwner {
        members[_member] = false;
    }

    function createProposal(
        string memory _title,
        string memory _descriptionHash,
        uint256 _amountRequested,
        address payable _recipient,
        uint256 _votingDurationDays
    ) external onlyMember {
        proposalCount++;
        proposals[proposalCount] = Proposal({
            id: proposalCount,
            title: _title,
            descriptionHash: _descriptionHash,
            amountRequested: _amountRequested,
            recipient: _recipient,
            votesFor: 0,
            votesAgainst: 0,
            executed: false,
            endTime: block.timestamp + (_votingDurationDays * 1 days)
        });

        emit ProposalCreated(proposalCount, _title, _amountRequested);
        emit TelemetryEmitted("proposal_created", _descriptionHash);
    }

    function vote(uint256 _proposalId, bool _inFavor) external onlyMember {
        Proposal storage p = proposals[_proposalId];
        require(block.timestamp < p.endTime, "Voting has ended");
        require(!p.executed, "Already executed");

        // Simple 1-person-1-vote for now. In reality, would track hasVoted per proposal.
        if (_inFavor) {
            p.votesFor++;
        } else {
            p.votesAgainst++;
        }

        emit Voted(_proposalId, msg.sender, _inFavor);
    }

    function executeProposal(uint256 _proposalId) external onlyMember {
        Proposal storage p = proposals[_proposalId];
        require(block.timestamp >= p.endTime, "Voting not ended");
        require(!p.executed, "Already executed");
        require(p.votesFor > p.votesAgainst, "Proposal rejected");
        require(address(this).balance >= p.amountRequested, "Insufficient funds");

        p.executed = true;
        p.recipient.transfer(p.amountRequested);

        emit ProposalExecuted(_proposalId, p.recipient, p.amountRequested);
        emit TelemetryEmitted("proposal_executed", p.descriptionHash);
    }
}
