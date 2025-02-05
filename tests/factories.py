"""Test data factories for generating test objects."""
import factory
from factory.alchemy import SQLAlchemyModelFactory
from product_order_api.models.product import Product
from product_order_api.models.order import Order, OrderItem


class ProductFactory(SQLAlchemyModelFactory):
    """Factory for generating test Product instances."""
    
    class Meta:
        model = Product
        sqlalchemy_session = None  # Set dynamically
        sqlalchemy_session_persistence = "commit"

    name = factory.Sequence(lambda n: f"Test Product {n}")
    description = factory.Sequence(lambda n: f"Description for test product {n}")
    price = factory.Sequence(lambda n: 10.0 + n)
    stock = factory.Sequence(lambda n: 100 + n)

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override _create to handle session."""
        session = kwargs.pop("session", None)
        if session:
            cls._meta.sqlalchemy_session = session
        return super()._create(model_class, *args, **kwargs)


class OrderFactory(SQLAlchemyModelFactory):
    """Factory for generating test Order instances."""
    
    class Meta:
        model = Order
        sqlalchemy_session = None  # Set dynamically
        sqlalchemy_session_persistence = "commit"

    customer_name = factory.Sequence(lambda n: f"Customer {n}")
    customer_email = factory.Sequence(lambda n: f"customer{n}@example.com")
    status = "pending"
    total_amount = 0.0  # Default total amount

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override _create to handle session."""
        session = kwargs.pop("session", None)
        if session:
            cls._meta.sqlalchemy_session = session
        return super()._create(model_class, *args, **kwargs)


class OrderItemFactory(SQLAlchemyModelFactory):
    """Factory for generating test OrderItem instances."""
    
    class Meta:
        model = OrderItem
        sqlalchemy_session = None  # Set dynamically
        sqlalchemy_session_persistence = "commit"

    order = factory.SubFactory(OrderFactory)
    product = factory.SubFactory(ProductFactory)
    quantity = factory.Sequence(lambda n: n + 1)
    unit_price = factory.SelfAttribute('product.price')
    subtotal = factory.LazyAttribute(lambda obj: obj.quantity * obj.unit_price)

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override _create to handle session."""
        session = kwargs.pop("session", None)
        if session:
            cls._meta.sqlalchemy_session = session
            if "order" in kwargs and isinstance(kwargs["order"], OrderFactory):
                kwargs["order"]._meta.sqlalchemy_session = session
            if "product" in kwargs and isinstance(kwargs["product"], ProductFactory):
                kwargs["product"]._meta.sqlalchemy_session = session
        return super()._create(model_class, *args, **kwargs)
