def prodmessage(company, product, perish, batch, man_date: str | None, exp_date: str|None):
    if perish == True:
        return f"({product} is an authentic product from {company} with the batch code {batch}. {product} is manufactured on {man_date} and would expire on {exp_date}. Thank you for your patronage.)"
    else:
        return f"({product} is an authentic product from {company} with the batch code {batch}. Thank you for your patronage.)"