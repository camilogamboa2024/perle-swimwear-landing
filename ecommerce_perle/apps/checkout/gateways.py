from dataclasses import dataclass


@dataclass
class PaymentResult:
    approved: bool
    reference: str
    message: str


class PaymentGateway:
    def charge(self, amount: int, currency: str, payload: dict) -> PaymentResult:
        raise NotImplementedError


class DummyGateway(PaymentGateway):
    def charge(self, amount: int, currency: str, payload: dict) -> PaymentResult:
        return PaymentResult(approved=True, reference='dummy-ref', message='Pago simulado')
