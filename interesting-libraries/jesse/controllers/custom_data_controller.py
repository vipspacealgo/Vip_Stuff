import os
import pandas as pd
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Header, HTTPException
from starlette.responses import JSONResponse
from pydantic import BaseModel

from jesse.services import auth as authenticator
import jesse.helpers as jh

router = APIRouter(prefix="/custom-data", tags=["Custom Data"])


class CustomDataInfo(BaseModel):
    symbol: str
    filename: str
    rows: int
    start_date: str
    end_date: str


@router.post("/upload")
async def upload_custom_data(
    symbol: str,
    file: UploadFile = File(...),
    authorization: Optional[str] = Header(None)
) -> JSONResponse:
    """
    Upload custom data file (CSV or JSON) for a symbol
    """
    if not authenticator.is_valid_token(authorization):
        return authenticator.unauthorized_response()

    # Validate file type
    if not file.filename.endswith(('.csv', '.json')):
        raise HTTPException(
            status_code=400, 
            detail="Only CSV and JSON files are supported"
        )

    # Create custom_data directory if it doesn't exist
    custom_data_path = os.path.join(os.getcwd(), 'custom_data')
    if not os.path.exists(custom_data_path):
        os.makedirs(custom_data_path)

    # Save file with symbol name
    file_extension = file.filename.split('.')[-1]
    filename = f"{symbol}.{file_extension}"
    file_path = os.path.join(custom_data_path, filename)

    try:
        content = await file.read()
        with open(file_path, 'wb') as f:
            f.write(content)

        # Validate the file format
        if file_extension == 'csv':
            df = pd.read_csv(file_path)
        else:
            df = pd.read_json(file_path)

        # Check required columns
        required_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            os.remove(file_path)  # Remove invalid file
            raise HTTPException(
                status_code=400,
                detail=f"Missing required columns: {', '.join(missing_columns)}"
            )

        # Get file info
        rows = len(df)
        start_date = str(pd.to_datetime(df['timestamp']).min().date())
        end_date = str(pd.to_datetime(df['timestamp']).max().date())

        return JSONResponse({
            'message': f'Custom data for {symbol} uploaded successfully',
            'filename': filename,
            'rows': rows,
            'start_date': start_date,
            'end_date': end_date
        }, status_code=200)

    except Exception as e:
        # Clean up file if there was an error
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/list")
def list_custom_data(authorization: Optional[str] = Header(None)) -> JSONResponse:
    """
    List all available custom data files
    """
    if not authenticator.is_valid_token(authorization):
        return authenticator.unauthorized_response()

    custom_data_path = os.path.join(os.getcwd(), 'custom_data')
    
    if not os.path.exists(custom_data_path):
        return JSONResponse({'data': []}, status_code=200)

    custom_data_files = []
    
    for filename in os.listdir(custom_data_path):
        if filename.endswith(('.csv', '.json')):
            symbol = filename.rsplit('.', 1)[0]
            file_path = os.path.join(custom_data_path, filename)
            
            try:
                if filename.endswith('.csv'):
                    df = pd.read_csv(file_path)
                else:
                    df = pd.read_json(file_path)
                
                rows = len(df)
                start_date = str(pd.to_datetime(df['timestamp']).min().date())
                end_date = str(pd.to_datetime(df['timestamp']).max().date())
                
                custom_data_files.append({
                    'symbol': symbol,
                    'filename': filename,
                    'rows': rows,
                    'start_date': start_date,
                    'end_date': end_date
                })
            except Exception:
                # Skip files that can't be processed
                continue

    return JSONResponse({'data': custom_data_files}, status_code=200)


@router.delete("/delete/{symbol}")
def delete_custom_data(symbol: str, authorization: Optional[str] = Header(None)) -> JSONResponse:
    """
    Delete custom data for a symbol
    """
    if not authenticator.is_valid_token(authorization):
        return authenticator.unauthorized_response()

    custom_data_path = os.path.join(os.getcwd(), 'custom_data')
    
    # Check for both CSV and JSON files
    for ext in ['csv', 'json']:
        file_path = os.path.join(custom_data_path, f"{symbol}.{ext}")
        if os.path.exists(file_path):
            os.remove(file_path)
            return JSONResponse({
                'message': f'Custom data for {symbol} deleted successfully'
            }, status_code=200)
    
    raise HTTPException(status_code=404, detail=f"No custom data found for symbol: {symbol}")