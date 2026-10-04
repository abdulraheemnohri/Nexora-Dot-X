import time
async def benchmark(engine,prompt="Return Nexora OK"):
    start=time.perf_counter(); text=await engine.generate(prompt); elapsed=time.perf_counter()-start
    tokens=max(1,len(text.split()))
    return {"seconds":round(elapsed,3),"output_tokens_estimate":tokens,"tokens_per_second":round(tokens/elapsed,2) if elapsed else 0}
