def prodmessage(company, product, perish, batch, fda: str | None, stands: str | None,  man_date: str | None, exp_date: str|None):
    
    if perish and len(fda) > 2 and len(stands) > 2:
        return f"({product} is an authentic product from {company} with the batch code {batch}, FDA number {fda} and Standards Authority number {stands}. {product} is manufactured on {man_date} and would expire on {exp_date}. Thank you for your patronage.)"
    elif perish and len(fda) > 2:
        return f"({product} is an authentic product from {company} with the batch code {batch} and FDA number {fda}. {product} is manufactured on {man_date} and would expire on {exp_date}. Thank you for your patronage.)"
    elif perish and len(stands) > 2:
        return f"({product} is an authentic product from {company} with the batch code {batch} and Standards Authority number {stands}. {product} is manufactured on {man_date} and would expire on {exp_date}. Thank you for your patronage.)"
    elif len(fda) > 2 and len(stands) > 2:
        return f"({product} is an authentic product from {company} with the batch code {batch}, FDA number {fda} and Standards Authority number {stands}. Thank you for your patronage.)"
    elif len(stands) > 2:
        return f"({product} is an authentic product from {company} with the batch code {batch} and Standards Authority number {stands}. Thank you for your patronage.)"
    elif len(fda) > 2:
        return f"({product} is an authentic product from {company} with the batch code {batch} and FDA number {fda}. Thank you for your patronage.)"
    elif perish:
        return f"({product} is an authentic product from {company} with the batch code {batch}. {product} is manufactured on {man_date} and would expire on {exp_date}. Thank you for your patronage.)"
    else:
        return f"({product} is an authentic product from {company} with the batch code {batch}. Thank you for your patronage.)"