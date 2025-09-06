class ValidationError(Exception):
    pass

def get_user_input(
    prompt, 
    input_type="string",
    default=None,
    choices=None,
    validators=None,
    password=False,
    confirm=False,
    max_attempts=3,
    help_text=None,
    required=True
):
    display_prompt = prompt
    if default is not None and not password:
        display_prompt = f"{prompt} [{default}]: "
    elif default is not None and password:
        display_prompt = f"{prompt} [leave empty to use saved password]: "
    else:
        display_prompt = f"{prompt}: "
    
    if choices:
        choices_str = "/".join(str(choice) for choice in choices)
        display_prompt = f"{display_prompt} ({choices_str}) "
    
    attempts = 0
    
    while attempts < max_attempts:
        try:
            if password:
                user_input = "hidden_password_input"
            else:
                user_input = input(display_prompt)
            
            if user_input == "?" and help_text:
                print(f"\nHelp: {help_text}\n")
                continue
            
            if not user_input:
                if default is not None:
                    return default
                elif not required:
                    return None
                else:
                    raise ValidationError("This field is required.")
            
            converted_input = _convert_input(user_input, input_type)
            
            if choices and converted_input not in choices:
                raise ValidationError(
                    f"Input must be one of: {', '.join(str(c) for c in choices)}"
                )
            
            if validators:
                for validator in validators:
                    validator_result = validator(converted_input)
                    if validator_result is not True:
                        error_msg = validator_result if isinstance(validator_result, str) else "Validation failed"
                        raise ValidationError(error_msg)
            
            if confirm and not password:
                confirm_input = input(f"Confirm {prompt}: ")
                if confirm_input != user_input:
                    raise ValidationError("Inputs do not match. Please try again.")
            elif confirm and password:
                confirm_input = "hidden_password_confirmation"
                if confirm_input != user_input:
                    raise ValidationError("Passwords do not match. Please try again.")
            
            return converted_input
            
        except ValidationError as e:
            attempts += 1
            if attempts < max_attempts:
                print(f"Error: {str(e)} ({attempts}/{max_attempts} attempts)")
            else:
                raise ValidationError(f"Maximum attempts ({max_attempts}) exceeded. Last error: {str(e)}")
                
        except Exception as e:
            attempts += 1
            if attempts < max_attempts:
                print(f"Error: {str(e)} ({attempts}/{max_attempts} attempts)")
            else:
                raise ValidationError(f"Maximum attempts ({max_attempts}) exceeded. Last error: {str(e)}")

def _convert_input(value, input_type):
    try:
        if input_type.lower() == "string":
            return str(value)
            
        elif input_type.lower() == "int":
            return int(value)
            
        elif input_type.lower() == "float":
            return float(value)
            
        elif input_type.lower() == "bool":
            if value.lower() in ["yes", "y", "true", "t", "1"]:
                return True
            elif value.lower() in ["no", "n", "false", "f", "0"]:
                return False
            else:
                raise ValidationError("Please enter Yes/No, True/False, or 1/0")
                
        elif input_type.lower() == "email":
            if "@" not in value:
                raise ValidationError("Invalid email address format")
            return value
            
        else:
            return value
            
    except ValidationError:
        raise
        
    except Exception as e:
        raise ValidationError(f"Invalid {input_type}: {str(e)}")