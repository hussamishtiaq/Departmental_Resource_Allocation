export const ROLE_LABELS = {
  hod: "Head of Department",
  department_admin: "Department Admin",
  lab_staff: "Lab Staff",
  faculty: "Faculty",
  student: "Student",
};

export const roleLabel = (name) => ROLE_LABELS[name] ?? name;

export const KIND_LABELS = { room: "Room", laboratory: "Laboratory", equipment: "Equipment" };
export const STATUS_LABELS = { available: "Available", maintenance: "Under maintenance", damaged: "Damaged", retired: "Retired" };
export const STATUS_TONES = { available: "green", maintenance: "yellow", damaged: "red", retired: "gray" };

export const RESERVATION_TONES = { pending: "yellow", approved: "green", rejected: "red", cancelled: "gray" };
