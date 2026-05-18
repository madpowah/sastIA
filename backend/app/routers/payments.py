import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Audit, Payment, PaymentStatus, PaymentMethod
from app.schemas import PaymentIntentRequest, PaymentIntentResponse, PaymentResponse
from app.auth import get_current_user
from app.config import get_settings

settings = get_settings()
router = APIRouter(prefix="/api/payments", tags=["Payments"])


@router.post("/create-intent", response_model=PaymentIntentResponse)
def create_payment_intent(
    data: PaymentIntentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    audit = db.query(Audit).filter(Audit.id == data.audit_id, Audit.user_id == current_user.id).first()
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")

    payment = Payment(
        audit_id=audit.id,
        user_id=current_user.id,
        amount=data.price_cents,
        currency="EUR",
        status=PaymentStatus.PENDING,
        payment_method=PaymentMethod.STRIPE,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)

    return PaymentIntentResponse(
        client_secret=f"pi_mock_{payment.id}_secret_placeholder",
        payment_id=payment.id,
        amount=data.price_cents,
    )


@router.post("/{payment_id}/confirm", response_model=PaymentResponse)
def confirm_payment(
    payment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    payment = db.query(Payment).filter(
        Payment.id == payment_id,
        Payment.user_id == current_user.id
    ).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    if payment.status != PaymentStatus.PENDING:
        raise HTTPException(status_code=400, detail="Payment already processed")

    payment.status = PaymentStatus.COMPLETED
    db.commit()
    db.refresh(payment)

    return PaymentResponse.model_validate(payment)


@router.get("/", response_model=list[PaymentResponse])
def list_payments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    payments = db.query(Payment).filter(
        Payment.user_id == current_user.id
    ).order_by(Payment.created_at.desc()).all()
    return [PaymentResponse.model_validate(p) for p in payments]
