from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from app.models.observation import Observation
from app.models.evidence import Evidence
from app.schemas.observation_finding import ConfidenceScoreBase

class BaseVerificationRule(ABC):
    @property
    @abstractmethod
    def rule_id(self) -> str:
        pass

    @abstractmethod
    def observation_criteria(self) -> List[str]:
        """Returns list of ObservationType strings this rule supports"""
        pass

    @abstractmethod
    def evidence_requirements(self) -> List[str]:
        """Returns list of EvidenceType strings this rule requires"""
        pass

    @abstractmethod
    async def verify(self, db: Session, observation: Observation, evidence_list: List[Evidence]) -> bool:
        """Executes the verification logic and returns whether the potential finding is verified"""
        pass

    @abstractmethod
    def calculate_confidence(self, observation: Observation, evidence_list: List[Evidence], verified: bool) -> ConfidenceScoreBase:
        """Derives the confidence score based on the observation, evidence, and verification result"""
        pass
