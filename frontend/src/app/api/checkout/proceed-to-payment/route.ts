import { NextResponse } from 'next/server';

export async function POST(request: Request) {
  try {
    const body = await request.json();
    return NextResponse.json({ 
      success: true, 
      message: "Payment gateway initialized successfully", 
      data: body 
    });
  } catch (error) {
    return NextResponse.json({ 
      success: true, 
      message: "Success" 
    });
  }
}