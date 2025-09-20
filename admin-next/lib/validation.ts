import { z } from "zod"

// Shared enums
export const ApiKeyRoleSchema = z.enum(["user", "admin"]) // aligns with types

// User schemas
export const CreateUserFormSchema = z.object({
  name: z.string().trim().min(1, "Name is required"),
  email: z
    .string()
    .trim()
    .optional()
    .transform((v) => (v === "" ? undefined : v))
    .refine((v) => (v ? /.+@.+\..+/.test(v) : true), {
      message: "Email must be valid",
    }),
})

export const UpdateUserFormSchema = z
  .object({
    name: z.string().trim().optional(),
    email: z
      .string()
      .trim()
      .optional()
      .transform((v) => (v === "" ? undefined : v))
      .refine((v) => (v ? /.+@.+\..+/.test(v) : true), {
        message: "Email must be valid",
      }),
  })
  .refine((data) => Boolean(data.name) || Boolean(data.email), {
    message: "Provide a name or email",
    path: ["name"],
  })

// Helper to coerce number from input or empty string → undefined
const optionalIntFromString = z
  .string()
  .trim()
  .optional()
  .transform((v) => (v ? Number.parseInt(v, 10) : undefined))
  .refine((v) => (v === undefined ? true : Number.isFinite(v) && v >= 0), {
    message: "Must be a non-negative integer",
  })

// Create Key (Modal) form schema
export const CreateKeyFormSchema = z.object({
  user_id: z.string().uuid("Select a valid user"),
  name: z.string().trim().min(1, "Key name is required"),
  role: ApiKeyRoleSchema,
  monthlyQuota: optionalIntFromString,
  dailyQuota: optionalIntFromString,
})

// Inline Create Key on User Detail page
export const CreateKeyInlineFormSchema = z.object({
  name: z.string().trim().min(1, "Key name is required"),
  role: ApiKeyRoleSchema,
  monthlyQuota: optionalIntFromString,
  dailyQuota: optionalIntFromString,
})

export function formatZodError(err: z.ZodError): string {
  const { fieldErrors, formErrors } = err.flatten()
  const fieldMsgs = Object.values(fieldErrors)
    .flat()
    .filter(Boolean)
  const msgs = [...formErrors, ...fieldMsgs]
  return msgs.length ? msgs.join("; ") : "Invalid form input"
}

