import asyncio
from db_manager import get_patsan

async def test():
    print("Testing get_patsan function...")
    try:
        p = await get_patsan(123456)
        print('✅ Success! User data:', p)
        print('Type:', type(p))
        print('Keys:', list(p.keys()) if p else 'None')
        print('User ID:', p.get('user_id') if p else 'None')
        return True
    except Exception as e:
        print('❌ Error:', e)
        return False

if __name__ == "__main__":
    result = asyncio.run(test())
    if result:
        print("\n🎉 Test passed! The bug is fixed.")
    else:
        print("\n💥 Test failed!")