from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.encoders import jsonable_encoder
from fastapi_jwt_auth import AuthJWT
from models import User, Order
from schemas import OrderModel, OrderStatusModel
from database import Session, engine

order_router = APIRouter(
    prefix="/orders",
    tags=['orders']
)

session = Session(bind = engine)



@order_router.get("/")
async def hello(Authorize: AuthJWT = Depends()):
    try:
        Authorize.jwt_required

    except Exception as e:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "Invalid Token"
        )
    
    return {"message": "Hello World"}



@order_router.post('/order', status_code = status.HTTP_201_CREATED)
async def place_an_order(order: OrderModel, Authorize: AuthJWT = Depends()):
    """
        ## Place an order
        ## Permission: User, Staff

        ## Requires the following
        ## - quantity
        ## - pizza_size
    """
    try:
        Authorize.jwt_required

    except Exception as e:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "Invalid Token"
        )
    
    current_user = Authorize.get_jwt_subject()

    user = session.query(User).filter(User.username == current_user).first()

    new_order = Order(
        pizza_size = order.pizza_size,
        quantity = order.quantity
    )

    new_order.user = user

    session.add(new_order)
    session.commit()

    response = {
        "pizza_size": new_order.pizza_size.value,
        "quantity": new_order.quantity,
        "id": new_order.id,
        "order_status": new_order.order_status.value
    }

    return jsonable_encoder(response)



@order_router.get('/orders')
async def list_all_orders(Authorize: AuthJWT = Depends()):
    """
        ## List all orders
        ## Permission: Staff
    """
    try:
        Authorize.jwt_required()

    except Exception as e:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "Invalid Token"
        )
    
    current_user = Authorize.get_jwt_subject()

    user = session.query(User).filter(User.username == current_user).first()

    if user.is_staff:
        orders = session.query(Order).all()
        return jsonable_encoder([{
            "id": order.id,
            "quantity": order.quantity,
            "order_status": order.order_status.value,
            "pizza_size": order.pizza_size.value,
            "user_id": order.user_id
        } for order in orders])
    
    raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "User is not a superuser"
    )



@order_router.get('/order/{id}')
async def get_order_by_id(id: int, Authorize: AuthJWT = Depends()):
    """
        ## Get a specific order based on id
        ## Permission: Staff
    """
    try:
        Authorize.jwt_required()

    except Exception as e:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "Invalid Token"
        ) 
    
    current_user = Authorize.get_jwt_subject()

    user = session.query(User).filter(User.username == current_user).first()

    if user.is_staff:
        order = session.query(Order).filter(Order.id == id).first()
        
        if order is None:
            raise HTTPException(
                status_code = status.HTTP_400_BAD_REQUEST,
                detail = f"Order with order_id {id} is not found"
            )
        
        response = {
            "id": order.id,
            "quantity": order.quantity,
            "order_status": order.order_status.value,
            "pizza_size": order.pizza_size.value,
            "user_id": order.user_id
        }
        return jsonable_encoder(response)
    
    raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "User is not a superuser"
    )
    


@order_router.get('/user/orders')
async def get_user_orders(Authorize: AuthJWT = Depends()):
    """
        ## List user's orders
        ## Permission: User, Staff
    """
    try:
        Authorize.jwt_required()

    except Exception as e:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "Invalid Token"
        ) 

    current_user = Authorize.get_jwt_subject()

    user = session.query(User).filter(User.username == current_user).first()

    if user.orders is None:
        return jsonable_encoder(
            {
                "message": "The user does not have any orders"
            }
        )

    return jsonable_encoder([{
            "id": order.id,
            "quantity": order.quantity,
            "order_status": order.order_status.value,
            "pizza_size": order.pizza_size.value,
            "user_id": order.user_id
        } for order in user.orders])



@order_router.get('/user/orders/{id}')
async def get_specific_order(id: int, Authorize: AuthJWT = Depends()):
    """
        ## Get a user's specific order based on id
        ## Permission: User, Staff
    """
    try:
        Authorize.jwt_required()

    except Exception as e:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "Invalid Token"
        )
    
    current_user = Authorize.get_jwt_subject()

    user = session.query(User).filter(User.username == current_user).first()

    if user.orders is None:
        return jsonable_encoder(
            {
                "message": "The user does not have any orders"
            }
        )
    
    order = next((order for order in user.orders if order.id == id), None)

    if order == None:
        return jsonable_encoder(
            {
                "message": f"User does not have an order with order_id {id}"
            }
        )
    
    return jsonable_encoder(
        {
            "id": order.id,
            "quantity": order.quantity,
            "order_status": order.order_status.value,
            "pizza_size": order.pizza_size.value,
            "user_id": order.user_id
        }
    )



@order_router.put('/order/update/{id}')
async def update_order(id: int, order: OrderModel, Authorize: AuthJWT = Depends()):
    """
        ## Update order details
        ## Permission: User, Staff
    """
    try:
        Authorize.jwt_required()

    except Exception as e:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "Invalid Token"
        )
    
    current_user = Authorize.get_jwt_subject()

    user = session.query(User).filter(User.username == current_user).first()

    order_to_update = session.query(Order).filter(Order.id == id).first()

    if "quantity" in order.__fields_set__ and order.quantity is not None:
        if order.quantity > 0:
            order_to_update.quantity = order.quantity
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Please provide a value for quantity greater than 0"
            )
        
    if "pizza_size" in order.__fields_set__ and order.pizza_size is not None:
        pizza_size_upper = order.pizza_size.upper()
        if pizza_size_upper in ["SMALL", "MEDIUM", "LARGE", "EXTRA-LARGE"]:
            order_to_update.pizza_size = pizza_size_upper
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Please provide a value for pizza size from ['SMALL', 'MEDIUM', 'LARGE', 'EXTRA-LARGE']"
            )
    
    session.commit()

    return jsonable_encoder(
        {
            "id": order_to_update.id,
            "quantity": order_to_update.quantity,
            "order_status": order_to_update.order_status.value,
            "pizza_size": order_to_update.pizza_size.value,
            "user_id": order_to_update.user_id
        }
    )



@order_router.patch('/order/update/{id}')
async def update_order_status(id: int, order: OrderStatusModel, Authorize: AuthJWT = Depends()):
    """
        ## Update Order Status
        ## Permission: User, Staff

        ## Requires the following
        ## - qorder_status in ["PENDING", "IN-TRANSIT", "DELIVERED"]
    """
    try:
        Authorize.jwt_required()

    except Exception as e:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "Invalid Token"
        )
    
    current_user = Authorize.get_jwt_subject()

    user = session.query(User).filter(User.username == current_user).first()

    if user.is_staff:
        order_to_update = session.query(Order).filter(Order.id == id).first()

        if "order_status" in order.__fields_set__ and order.order_status is not None:
            if order.order_status in ['PENDING', 'IN-TRANSIT', 'DELIVERED']:
                order_to_update.order_status = order.order_status
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Please provide a value for order_status from ['PENDING', 'IN-TRANSIT', 'DELIVERED']"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Please provide a value for order_status from ['PENDING', 'IN-TRANSIT', 'DELIVERED']"
            )
        
        session.commit()

    return jsonable_encoder(
        {
            "id": order_to_update.id,
            "quantity": order_to_update.quantity,
            "order_status": order_to_update.order_status.value,
            "pizza_size": order_to_update.pizza_size.value,
            "user_id": order_to_update.user_id
        }
    )



@order_router.delete('/order/delete/{id}', status_code = status.HTTP_204_NO_CONTENT)
async def delete_order(id: int, Authorize: AuthJWT = Depends()):
    """
        ## Delete an order
        ## Permission: User, Staff
    """
    try:
        Authorize.jwt_required()

    except Exception as e:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "Invalid Token"
        )
    
    current_user = Authorize.get_jwt_subject()

    user = session.query(User).filter(User.username == current_user).first()

    order_to_delete = session.query(Order).filter(Order.id == id).first()

    session.delete(order_to_delete)
    session.commit()

    return jsonable_encoder(
        {
            "id": order_to_delete.id,
            "quantity": order_to_delete.quantity,
            "order_status": order_to_delete.order_status.value,
            "pizza_size": order_to_delete.pizza_size.value,
            "user_id": order_to_delete.user_id
        }
    )